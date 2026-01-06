import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst

# Initialize GStreamer
Gst.init(None)

# Check version
print(f"GStreamer version: {Gst.version_string()}")

# Create a simple pipeline to test
pipeline = Gst.parse_launch("videotestsrc ! autovideosink")
print("Pipeline created successfully!")