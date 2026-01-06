#!/usr/bin/env python3
import sys
import gi
import logging

gi.require_version("GLib", "2.0")
gi.require_version("GObject", "2.0")
gi.require_version("Gst", "1.0")

from gi.repository import Gst, GLib, GObject

# initiate looger
logging.basicConfig(level=logging.DEBUG, format="[%(name)s] [%(levelname)8s] - %(message)s")
logger = logging.getLogger(__name__)

# Initialize GStreamer
Gst.init(sys.argv[1:])

# Create the elements
source = Gst.ElementFactory.make("videotestsrc", "source")
sink = Gst.ElementFactory.make("autovideosink", "sink")
fltr = Gst.ElementFactory.make("vertigotv", "fltr")
convert = Gst.ElementFactory.make("videoconvert", "convert")

# Create the empty pipeline
pipeline = Gst.Pipeline.new("test-pipeline")

if not pipeline or not source or not sink:
    logger.error("Not all elements could be created.")
    sys.exit(1)

# Build the pipeline from Gst.Bin
pipeline.add(source)
pipeline.add(fltr)
pipeline.add(convert)
pipeline.add(sink)

if not source.link(fltr) or not fltr.link(convert) or not convert.link(sink): # link source to sink
    logger.error("Elements could not be linked.")
    sys.exit(1)


# Modify the source's properties
Gst.util_set_object_arg(source, "pattern", "0")
# Can alternatively be done using `source.props.pattern = 0` or `source.set_property("pattern",0)`

# Start playing
ret = pipeline.set_state(Gst.State.PLAYING)
if ret == Gst.StateChangeReturn.FAILURE:
    logger.error("Unable to set the pipeline to the playing state.")
    sys.exit(1)

# Wait for EOS or error
msg =  pipeline.get_bus().timed_pop_filtered(Gst.CLOCK_TIME_NONE, Gst.MessageType.ERROR | Gst.MessageType.EOS)

# Parse message (EOS or error)
if msg:
    if msg.type == Gst.MessageType.ERROR:
        err, debug_info = msg.parse_error()
        logger.error(f"Error received from element {msg.src.get_name()}: {err.message}")
        logger.error(f"Debugging information: {debug_info if debug_info else 'none'}")
    elif msg.type == Gst.MessageType.EOS:
        logger.info("End-Of-Stream reached.")
    else:
        # This should not happen as we only asked for ERRORs and EOS
        logger.error("Unexpected message received.")

pipeline.set_state(Gst.State.NULL)