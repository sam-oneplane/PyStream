"""
GStreamer + OpenCV + YOLO Object Detection and Tracking
This example demonstrates real-time object detection and tracking using:
- GStreamer for video stream capture (direct GStreamer, not OpenCV)
- OpenCV for image processing
- YOLOv8 for object detection
"""

import cv2
import numpy as np
from ultralytics import YOLO
import gi
from pathlib import Path

gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib

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
        
        # Frame storage
        self.current_frame = None
        self.frame_lock = False
        
    def create_gstreamer_pipeline(self, source):
        """
        Create GStreamer pipeline based on source type
        
        Args:
            source: Video source (file path, rtsp url, webcam index, etc.)
        """
        # Appsink that we'll pull samples from
        appsink_config = "appsink name=sink emit-signals=true sync=false max-buffers=1 drop=true"
        
        # Example pipelines for different sources
        if source.startswith('rtsp://'):
            # RTSP stream
            pipeline_str = (f"rtspsrc location={source} latency=0 ! "
                           f"decodebin ! videoconvert ! video/x-raw,format=BGR ! {appsink_config}")
        elif source.startswith('/dev/video') or source.isdigit():
            # Webcam
            device = source if source.startswith('/dev/video') else f'/dev/video{source}'
            pipeline_str = (f"v4l2src device={device} ! "
                           f"videoconvert ! video/x-raw,format=BGR ! {appsink_config}")
        elif source.startswith('http://') or source.startswith('https://'):
            # HTTP stream
            pipeline_str = (f"souphttpsrc location={source} ! "
                           f"decodebin ! videoconvert ! video/x-raw,format=BGR ! {appsink_config}")
        else:
            # File source - use absolute path
            abs_path = str(Path(source).resolve())
            pipeline_str = (f"filesrc location={abs_path} ! "
                           f"decodebin ! videoconvert ! video/x-raw,format=BGR ! {appsink_config}")
        
        return pipeline_str
    
    def _on_new_sample(self, sink):
        """Callback for new frame from appsink"""
        sample = sink.emit("pull-sample")
        if sample:
            buf = sample.get_buffer()
            caps = sample.get_caps()
            
            # Get frame dimensions from caps
            structure = caps.get_structure(0)
            width = structure.get_value('width')
            height = structure.get_value('height')
            
            # Extract buffer data
            result, map_info = buf.map(Gst.MapFlags.READ)
            if result:
                # Convert to numpy array
                frame_data = np.ndarray(
                    shape=(height, width, 3),
                    dtype=np.uint8,
                    buffer=map_info.data
                )
                
                # Store the frame (make a copy since buffer will be unmapped)
                if not self.frame_lock:
                    self.current_frame = frame_data.copy()
                
                buf.unmap(map_info)
        
        return Gst.FlowReturn.OK
    
    def start_stream(self):
        """Start video streaming and object detection"""
        # Create GStreamer pipeline
        pipeline_str = self.create_gstreamer_pipeline(self.stream_url)
        print(f"GStreamer Pipeline: {pipeline_str}")
        
        # Create pipeline
        pipeline = Gst.parse_launch(pipeline_str)
        
        # Get appsink element
        appsink = pipeline.get_by_name("sink")
        if not appsink:
            print("Error: Could not get appsink element")
            return
        
        # Connect to new-sample signal
        appsink.connect("new-sample", self._on_new_sample)
        
        # Start playing
        ret = pipeline.set_state(Gst.State.PLAYING)
        if ret == Gst.StateChangeReturn.FAILURE:
            print("Error: Unable to set pipeline to PLAYING state")
            return
        
        print("Video stream opened successfully")
        print("Press 'q' to quit, 's' to save frame")
        
        frame_count = 0
        
        try:
            while True:
                # Process the current frame if available
                if self.current_frame is not None:
                    self.frame_lock = True
                    frame = self.current_frame.copy()
                    self.frame_lock = False
                    
                    frame_count += 1
                    
                    # Run YOLO detection
                    results = self.model.track(frame, persist=True, verbose=False)
                    
                    # Process detections
                    annotated_frame = self._process_detections(frame, results[0])
                    
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
                else:
                    # Wait a bit if no frame yet
                    key = cv2.waitKey(10) & 0xFF
                    if key == ord('q'):
                        break
        
        finally:
            pipeline.set_state(Gst.State.NULL)
            cv2.destroyAllWindows()
            print("Stream closed")
            return 0
    
    def _process_detections(self, frame, results):
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
                np.random.seed(cls_id)
                color = tuple(map(int, np.random.randint(0, 255, 3)))
                
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


def main_wrapper(_, path):
    video_file = "".join(path)
    print(f'video file type {type(video_file)} path = {video_file}')
    # Create tracker with MP4 video file
    tracker = VideoStreamTracker(stream_url=video_file, model_path='yolov8n.pt')
    # Start tracking
    return tracker.start_stream()


# Example usage
if __name__ == "__main__":
    import sys
    import platform
    
    video_file: str = None
    # Check if video file path is provided
    if len(sys.argv) > 1:
        video_file = sys.argv[1]
        print(f"Processing video file: {video_file}")
    else:
        # Default video file
        parent_dir = Path.cwd().parent
        video_file = f"{parent_dir}/VideoSample/highway_1.mp4"
    
    
    # Use gst_macos_main on macOS
    if platform.system() == 'Darwin':
        sys.exit(Gst.macos_main(main_wrapper, video_file))
    else:
        
        # Create tracker with MP4 video file
        tracker = VideoStreamTracker(stream_url=video_file, model_path='yolov8n.pt')
        # Start tracking
        tracker.start_stream()