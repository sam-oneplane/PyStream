import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib

# Initialize GStreamer
Gst.init(None)

print(f"GStreamer version: {Gst.version_string()}")

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
    
