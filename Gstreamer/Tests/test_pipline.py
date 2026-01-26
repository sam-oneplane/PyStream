import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst

Gst.init(None)

# Test if we can create a simple pipeline
pipeline_str = "filesrc location=../VideoSample/highway_1.mp4 ! decodebin ! videoconvert ! video/x-raw,format=BGR ! appsink drop=1"

print("Testing GStreamer pipeline...")
pipeline = Gst.parse_launch(pipeline_str)

if pipeline:
    print("✓ Pipeline created successfully")
    ret = pipeline.set_state(Gst.State.PLAYING)
    print(f"State change return: {ret}")
    
    if ret == Gst.StateChangeReturn.FAILURE:
        print("✗ Failed to set pipeline to PLAYING state")
    else:
        print("✓ Pipeline is playing")
        
    # Get any error messages
    bus = pipeline.get_bus()
    msg = bus.timed_pop_filtered(1000000000, Gst.MessageType.ERROR | Gst.MessageType.WARNING)
    if msg:
        if msg.type == Gst.MessageType.ERROR:
            err, debug = msg.parse_error()
            print(f"✗ Error: {err}")
            print(f"  Debug: {debug}")
        elif msg.type == Gst.MessageType.WARNING:
            warn, debug = msg.parse_warning()
            print(f"⚠ Warning: {warn}")
    
    pipeline.set_state(Gst.State.NULL)
else:
    print("✗ Failed to create pipeline")

# Check available plugins
print("\nChecking required GStreamer plugins:")
required_plugins = ['filesrc', 'decodebin', 'videoconvert', 'appsink', 'qtdemux', 'avdec_h264']
for plugin_name in required_plugins:
    factory = Gst.ElementFactory.find(plugin_name)
    if factory:
        print(f"  ✓ {plugin_name}")
    else:
        print(f"  ✗ {plugin_name} - MISSING!")