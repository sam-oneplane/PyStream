import sys
import gi

gi.require_version('GLib', '2.0')
gi.require_version('GObject', '2.0')
gi.require_version('Gst', '1.0')

from gi.repository import Gst, GObject, GLib

pipeline = None
bus = None
message = None

class GstHello:
    def __init__(self, args) :
        # initialize GStreamer
        Gst.init(args)
        # build the pipeline
        self.pipeline = Gst.parse_launch(
            "playbin uri=https://gstreamer.freedesktop.org/data/media/sintel_trailer-480p.webm"
        )

    def __call__(self):
        # start playing
        self.pipeline.set_state(Gst.State.PLAYING)        
        # wait until EOS or error
        bus = self.pipeline.get_bus()
        msg = bus.timed_pop_filtered(
            Gst.CLOCK_TIME_NONE,
            Gst.MessageType.ERROR | Gst.MessageType.EOS
        )

        # free resources
        self.pipeline.set_state(Gst.State.NULL)


def main_wrapper(_, argv):
    """Wrapper function for gst_macos_main"""
    gst_hello = GstHello(argv[1:])
    return gst_hello()

if __name__ == "__main__":
    # Use gst_macos_main on macOS
    import platform
    if platform.system() == 'Darwin':
        sys.exit(Gst.macos_main(main_wrapper, sys.argv))
    else:
        gst_hello = GstHello(sys.argv[1:])
        sys.exit(gst_hello())
        
