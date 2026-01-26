import cv2
print("OpenCV version:", cv2.__version__)
print("GStreamer support:", cv2.VideoCapture(0).getBackendName() if hasattr(cv2.VideoCapture(0), 'getBackendName') else "Unknown")
print("Available backends:", [cv2.videoio_registry.getBackendName(b) for b in cv2.videoio_registry.getBackends()])