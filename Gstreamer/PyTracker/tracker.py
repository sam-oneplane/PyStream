"""
GStreamer + OpenCV + YOLO Object Detection and Tracking
This example demonstrates real-time object detection and tracking using:
- GStreamer for video stream capture
- OpenCV for image processing
- YOLOv8 for object detection
"""

import cv2
import numpy as np
from ultralytics import YOLO
import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst

class VideoStreamTracker:
    def __init__(self, stream_url, model_path='yolov8n.pt'):
        """
        Initialize the video stream tracker
        
        Args:
            stream_url: GStreamer pipeline or video source
            model_path: Path to YOLO model (default: yolov8n.pt)
        """
        # Initialize GStreamer
        Gst.init(None)
        
        # Load YOLO model
        print(f"Loading YOLO model: {model_path}")
        self.model = YOLO(model_path)
        
        # Store stream URL
        self.stream_url = stream_url
        
        # Tracking dictionary to store object trajectories
        self.tracks = {}
        self.track_id = 0
        
    def create_gstreamer_pipeline(self, source):
        """
        Create GStreamer pipeline string based on source type
        
        Args:
            source: Video source (file path, rtsp url, webcam index, etc.)
        """
        # Example pipelines for different sources
        if source.startswith('rtsp://'):
            # RTSP stream
            pipeline = f"rtspsrc location={source} latency=0 ! decodebin ! videoconvert ! appsink"
        elif source.startswith('/dev/video') or source.isdigit():
            # Webcam
            device = source if source.startswith('/dev/video') else f'/dev/video{source}'
            pipeline = f"v4l2src device={device} ! videoconvert ! appsink"
        elif source.startswith('http://') or source.startswith('https://'):
            # HTTP stream
            pipeline = f"souphttpsrc location={source} ! decodebin ! videoconvert ! appsink"
        else:
            # File source
            pipeline = f"filesrc location={source} ! decodebin ! videoconvert ! appsink"
        
        return pipeline
    
    def start_stream(self):
        """Start video streaming and object detection"""
        # Create GStreamer pipeline
        pipeline_str = self.create_gstreamer_pipeline(self.stream_url)
        print(f"GStreamer Pipeline: {pipeline_str}")
        
        # Open video capture with GStreamer
        cap = cv2.VideoCapture(pipeline_str, cv2.CAP_GSTREAMER)
        
        if not cap.isOpened():
            print("Error: Could not open video stream")
            return
        
        print("Video stream opened successfully")
        print("Press 'q' to quit, 's' to save frame")
        
        frame_count = 0
        
        try:
            while True:
                ret, frame = cap.read()
                
                if not ret:
                    print("Failed to grab frame or stream ended")
                    break
                
                frame_count += 1
                
                # Run YOLO detection
                results = self.model.track(frame, persist=True, verbose=False)
                
                # Process detections
                annotated_frame = self.process_detections(frame, results[0])
                
                # Display frame info
                cv2.putText(annotated_frame, f"Frame: {frame_count}", 
                           (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 
                           0.7, (0, 255, 0), 2)
                
                # Show the frame
                cv2.imshow('YOLO Object Tracking', annotated_frame)
                
                # Handle keyboard input
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord('s'):
                    filename = f"frame_{frame_count}.jpg"
                    cv2.imwrite(filename, annotated_frame)
                    print(f"Saved: {filename}")
        
        finally:
            cap.release()
            cv2.destroyAllWindows()
            print("Stream closed")
    
    def process_detections(self, frame, results):
        """
        Process YOLO detection results and draw annotations
        
        Args:
            frame: Input frame
            results: YOLO results object
        """
        annotated_frame = frame.copy()
        
        if results.boxes is not None and len(results.boxes) > 0:
            boxes = results.boxes.xyxy.cpu().numpy()  # Bounding boxes
            confidences = results.boxes.conf.cpu().numpy()  # Confidence scores
            class_ids = results.boxes.cls.cpu().numpy().astype(int)  # Class IDs
            
            # Get track IDs if available
            if results.boxes.id is not None:
                track_ids = results.boxes.id.cpu().numpy().astype(int)
            else:
                track_ids = [-1] * len(boxes)
            
            # Draw detections
            for box, conf, cls_id, track_id in zip(boxes, confidences, class_ids, track_ids):
                x1, y1, x2, y2 = map(int, box)
                
                # Get class name
                class_name = self.model.names[cls_id]
                
                # Color based on class
                color = self.get_color(cls_id)
                
                # Draw bounding box
                cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, 2)
                
                # Create label
                if track_id != -1:
                    label = f"ID:{track_id} {class_name} {conf:.2f}"
                else:
                    label = f"{class_name} {conf:.2f}"
                
                # Draw label background
                (label_w, label_h), _ = cv2.getTextSize(
                    label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2
                )
                cv2.rectangle(annotated_frame, (x1, y1 - label_h - 10), 
                             (x1 + label_w, y1), color, -1)
                
                # Draw label text
                cv2.putText(annotated_frame, label, (x1, y1 - 5), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
                
                # Draw center point
                center_x = (x1 + x2) // 2
                center_y = (y1 + y2) // 2
                cv2.circle(annotated_frame, (center_x, center_y), 4, color, -1)
        
        return annotated_frame
    
    def get_color(self, class_id):
        """Generate consistent color for each class"""
        np.random.seed(class_id)
        return tuple(map(int, np.random.randint(0, 255, 3)))


# Example usage
if __name__ == "__main__":
    import sys
    
    # Check if video file path is provided
    if len(sys.argv) > 1:
        video_file = sys.argv[1]
    else:
        # Default video file
        video_file = "video.mp4"
    
    print(f"Processing video file: {video_file}")
    
    # Create tracker with MP4 video file
    tracker = VideoStreamTracker(stream_url=video_file, model_path='yolov8n.pt')
    
    # Other source examples (uncomment to use):
    # tracker = VideoStreamTracker(stream_url="0")  # Webcam
    # tracker = VideoStreamTracker(stream_url="rtsp://username:password@ip:port/stream")  # RTSP
    # tracker = VideoStreamTracker(stream_url="http://example.com/stream.mjpg")  # HTTP
    
    # Start tracking
    tracker.start_stream()