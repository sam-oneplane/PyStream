import gi
import sys
from pathlib import Path

gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib

Gst.init(None)

# Use absolute path
video_file = "./VideoSample/highway_1.mp4"
abs_path = str(Path(video_file).resolve())

print(f"Video file: {abs_path}")
print(f"File exists: {Path(abs_path).exists()}")

# Test the exact pipeline that OpenCV will use
pipeline_str = f"filesrc location={abs_path} ! decodebin ! videoconvert ! video/x-raw,format=BGR ! appsink drop=1"

print(f"\nTesting pipeline: {pipeline_str}\n")

pipeline = Gst.parse_launch(pipeline_str)

# Create a main loop to catch messages
loop = GLib.MainLoop()

def on_message(bus, message):
    t = message.type
    if t == Gst.MessageType.ERROR:
        err, debug = message.parse_error()
        print(f"✗ ERROR: {err}")
        print(f"  Debug info: {debug}")
        loop.quit()
    elif t == Gst.MessageType.WARNING:
        warn, debug = message.parse_warning()
        print(f"⚠ WARNING: {warn}")
        print(f"  Debug info: {debug}")
    elif t == Gst.MessageType.EOS:
        print("✓ End of stream")
        loop.quit()
    elif t == Gst.MessageType.STATE_CHANGED:
        if message.src == pipeline:
            old, new, pending = message.parse_state_changed()
            print(f"Pipeline state: {old.value_nick} -> {new.value_nick}")
    return True

bus = pipeline.get_bus()
bus.add_signal_watch()
bus.connect("message", on_message)

print("Setting pipeline to PLAYING...")
ret = pipeline.set_state(Gst.State.PLAYING)

if ret == Gst.StateChangeReturn.FAILURE:
    print("✗ Unable to set the pipeline to PLAYING state")
    sys.exit(1)
elif ret == Gst.StateChangeReturn.NO_PREROLL:
    print("Pipeline is live")
elif ret == Gst.StateChangeReturn.ASYNC:
    print("Pipeline will preroll asynchronously")
else:
    print("✓ Pipeline set to PLAYING")

# Run for 2 seconds to see if it works
GLib.timeout_add_seconds(2, loop.quit)

try:
    loop.run()
except KeyboardInterrupt:
    pass

pipeline.set_state(Gst.State.NULL)
print("\nTest complete")