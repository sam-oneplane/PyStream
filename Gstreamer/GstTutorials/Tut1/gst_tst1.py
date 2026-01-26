
import sys
import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib


def main(_, argv: list):
# Initialize GStreamer
    Gst.init(argv[1:])

    # Create a simple pipeline
    pipeline = Gst.parse_launch("videotestsrc ! autovideosink")
    print("Pipeline created successfully!")

    # Start playing
    pipeline.set_state(Gst.State.PLAYING)
    print("Pipeline started, press Ctrl+C to stop...")

    # Create main loop
    loop = GLib.MainLoop()

    # Handle bus messages
    bus = pipeline.get_bus()
    bus.add_signal_watch()

    def on_message(bus, message):
        t = message.type
        if t == Gst.MessageType.EOS:
            print("End of stream")
            loop.quit()
        elif t == Gst.MessageType.ERROR:
            err, debug = message.parse_error()
            print(f"Error: {err}, {debug}")
            loop.quit()

    bus.connect("message", on_message)

    # Run the loop
    try:
        loop.run()
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        pipeline.set_state(Gst.State.NULL)
    
if __name__ == "__main__":
    # Use gst_macos_main on macOS
    import platform
    if platform.system() == 'Darwin':
        sys.exit(Gst.macos_main(main, sys.argv))
    else:
        sys.exit(main(sys.argv))
        
