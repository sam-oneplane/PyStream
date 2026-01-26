# Verify GStreamer is working at all
gst-inspect-1.0 --version

# Check if videotestsrc exists
gst-inspect-1.0 videotestsrc

# Check if autovideosink exists  
gst-inspect-1.0 autovideosink

# List what you have installed
brew list | grep gst

# Absolute simplest test
gst-launch-1.0 videotestsrc ! autovideosink

# If that works, then try
gst-launch-1.0 videotestsrc ! videoconvert ! autovideosink

# Check what autovideosink actually chooses
gst-launch-1.0 -v videotestsrc ! autovideosink
# Check gst-launch-1.0 with mac local camera
gst-launch-1.0 avfvideosrc ! osxvideosink