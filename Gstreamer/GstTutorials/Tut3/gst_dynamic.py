#!/usr/bin/env python3
import logging
import sys

import gi

gi.require_version("GLib", "2.0")
gi.require_version("GObject", "2.0")
gi.require_version("Gst", "1.0")

from gi.repository import Gst

class Loger:
    def __init__(self, logger, pipeline):
        self.logger = logger
        self.pipeline = pipeline

    def __call__(self, msg, terminate) -> bool:
        if msg.type == Gst.MessageType.ERROR:
            err, debug_info = msg.parse_error()
            self.logger.error(f"Error received from element {msg.src.get_name()}: {err.message}")
            self.logger.error(f"Debugging information: {debug_info if debug_info else 'none'}")
            terminate = True
        elif msg.type == Gst.MessageType.EOS:
            self.logger.info("End-Of-Stream reached.")
            terminate = True
        elif msg.type == Gst.MessageType.STATE_CHANGED:
          # We are only interested in state-changed messages from the pipeline
            if msg.src == self.pipeline:
                old_state, new_state, pending_state = msg.parse_state_changed()
                self.logger.info(f"Pipeline state changed from {old_state.value_nick}, to {new_state.value_nick}")
        else:
            # We should not reach here
            self.logger.error("Unexpected message received.")
            terminate = True
    
        return terminate
    


class PadHandler:
    def __init__(self, logger, audio_convert, video_convert):
        self.logger = logger
        self.audio_convert = audio_convert
        self.video_convert = video_convert

    def __call__(self, src, new_pad):
        self.logger.info(f"Received new pad '{new_pad.get_name()}' from '{src.get_name()}'")
        # Check the new pad's type
        new_pad_caps = new_pad.get_current_caps()
        new_pad_struct = new_pad_caps.get_structure(0)
        new_pad_type = new_pad_struct.get_name()
        
        self.logger.info(f"Pad type: {new_pad_type}")

        # Link audio pads
        if new_pad_type.startswith("audio/x-raw"):
            audio_sink_pad = self.audio_convert.get_static_pad("sink")
            if audio_sink_pad.is_linked():
                self.logger.info("Audio pad already linked. Ignoring.")
                return
            
            ret = new_pad.link(audio_sink_pad)
            if ret != Gst.PadLinkReturn.OK:
                self.logger.error(f"Audio link failed: {ret}")
            else:
                self.logger.info("Audio link succeeded")
        
        # Link video pads
        elif new_pad_type.startswith("video/x-raw"):
            video_sink_pad = self.video_convert.get_static_pad("sink")
            if video_sink_pad.is_linked():
                self.logger.info("Video pad already linked. Ignoring.")
                return
            
            ret = new_pad.link(video_sink_pad)
            if ret != Gst.PadLinkReturn.OK:
                self.logger.error(f"Video link failed: {ret}")
            else:
                self.logger.info("Video link succeeded")
        else:
            self.logger.info(f"Unknown pad type '{new_pad_type}'. Ignoring.")        
                

def main(_, args):                
        
    logging.basicConfig(level=logging.DEBUG, format="[%(name)s] [%(levelname)8s] - %(message)s")
    logger = logging.getLogger(__name__)

    # Initialize GStreamer
    Gst.init(args[1:])

    # Create the elements
    source = Gst.ElementFactory.make("uridecodebin", "source")
    # Audio
    audio_convert = Gst.ElementFactory.make("audioconvert", "audio_convert")
    audio_resample = Gst.ElementFactory.make("audioresample", "audio_resample")
    audio_sink = Gst.ElementFactory.make("autoaudiosink", "audio_sink")
    # Video elements
    video_convert = Gst.ElementFactory.make("videoconvert", "video_convert")
    video_sink = Gst.ElementFactory.make("autovideosink", "video_sink")

    # Create the empty pipeline
    pipeline = Gst.Pipeline.new("test-pipeline")

    if not all([pipeline, source, audio_convert, audio_resample, audio_sink, video_convert, video_sink]):
        logger.error("Not all elements could be created.")
        sys.exit(1)
        

    # Build the pipeline. Note that we are NOT linking the source at this
    # point. We will do it later.
    pipeline.add(source)
    pipeline.add(audio_convert)
    pipeline.add(audio_resample)
    pipeline.add(audio_sink)
    pipeline.add(video_convert)
    pipeline.add(video_sink)

    if not audio_convert.link(audio_resample) or not audio_resample.link(audio_sink):
        logger.error("Audio Elements could not be linked.")
        sys.exit(1)
        
    # Link video chain
    if not video_convert.link(video_sink):
        logger.error("Video elements could not be linked.")
        sys.exit(1)

    # Set the URI to play
    source.set_property("uri", "https://www.freedesktop.org/software/gstreamer-sdk/data/media/sintel_trailer-480p.webm")

    # Connect source to the pad_added signal with pad_handler callback func obj
    pad_handler = PadHandler(logger, audio_convert, video_convert)
    source.connect("pad-added", pad_handler)

    # Start playing
    ret = pipeline.set_state(Gst.State.PLAYING)
    if ret == Gst.StateChangeReturn.FAILURE:
        logger.error("Unable to set the pipeline to the playing state.")
        sys.exit(1)

    # Listen to the bus
    bus = pipeline.get_bus()
    terminate = False

    while not terminate:
        msg = bus.timed_pop_filtered(1 * Gst.SECOND, Gst.MessageType.STATE_CHANGED | Gst.MessageType.ERROR | Gst.MessageType.EOS)

        # Parse message
        if msg:
            loger = Loger(logger, pipeline)
            terminate = loger(msg, terminate)
            
    pipeline.set_state(Gst.State.NULL)
    return 0


if __name__ == "__main__":
    # Use gst_macos_main on macOS
    import platform
    if platform.system() == 'Darwin':
        sys.exit(Gst.macos_main(main, sys.argv))
    else:
        sys.exit(main())