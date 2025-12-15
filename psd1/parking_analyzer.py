#!/usr/bin/env python3
"""
Parking Lot Monitoring System
Main application for real-time parking space detection and occupancy tracking.
"""

import argparse
import cv2
import numpy as np
import time
import sys
from datetime import datetime
from typing import Optional
import threading

# Import custom modules
from parking_space import ParkingSpaceManager
from vehicle_detector import VehicleDetector, SimpleVehicleDetector
from config_manager import ConfigManager
from logger import ParkingLogger
from visualizer import Visualizer


class ParkingAnalyzer:
    """Main parking lot analyzer application"""
    
    def __init__(self, config_path: str, confidence_threshold: float = 0.5,
                 min_occupancy_ratio: float = 0.2, fps_limit: int = 30,
                 use_simple_detector: bool = False, device: str = 'cpu'):
        """
        Initialize the parking analyzer.
        
        Args:
            config_path: Path to parking spaces configuration file
            confidence_threshold: Vehicle detection confidence threshold
            min_occupancy_ratio: Minimum occupancy ratio for space classification (0.2 = 20%)
            fps_limit: Maximum FPS for processing
            use_simple_detector: Use simple background subtraction instead of YOLO
            device: Device for YOLO ('cpu', 'cuda', 'mps')
        """
        self.config_path = config_path
        self.confidence_threshold = confidence_threshold
        self.fps_limit = fps_limit
        self.frame_time = 1.0 / fps_limit if fps_limit > 0 else 0
        
        # Load parking spaces
        print(f"Loading parking spaces from: {config_path}")
        spaces = ConfigManager.load_spaces(config_path)
        self.space_manager = ParkingSpaceManager(spaces)
        print(f"Loaded {len(spaces)} parking spaces")
        
        # Initialize vehicle detector
        if use_simple_detector:
            print("Using simple background subtraction detector")
            self.detector = SimpleVehicleDetector(confidence_threshold)
        else:
            try:
                print("Initializing YOLOv8 detector...")
                self.detector = VehicleDetector(
                    confidence_threshold=confidence_threshold,
                    device=device
                )
                print("YOLOv8 detector initialized successfully")
            except Exception as e:
                print(f"Warning: Could not initialize YOLOv8: {e}")
                print("Falling back to simple detector")
                self.detector = SimpleVehicleDetector(confidence_threshold)
        
        # Initialize logger and visualizer
        self.logger = ParkingLogger()
        self.visualizer = Visualizer(show_detections=True, show_ids=True)
        
        # Performance tracking
        self.frame_count = 0
        self.fps = 0.0
        self.last_fps_time = time.time()
        
    def preprocess_frame(self, frame: np.ndarray) -> np.ndarray:
        """
        Preprocess frame for better detection (gamma correction, CLAHE, etc.).
        
        Args:
            frame: Input frame
            
        Returns:
            Preprocessed frame
        """
        # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization) for low-light
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        enhanced = cv2.merge([l, a, b])
        enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
        
        return enhanced
    
    def process_frame(self, frame: np.ndarray, timestamp: Optional[datetime] = None) -> np.ndarray:
        """
        Process a single frame: detect vehicles and update parking spaces.
        
        Args:
            frame: Input frame
            timestamp: Current timestamp
            
        Returns:
            Annotated frame
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        # Preprocess frame
        processed_frame = self.preprocess_frame(frame)
        
        # Detect vehicles
        vehicle_bboxes, vehicle_centroids, vehicle_classes, confidences = \
            self.detector.detect(processed_frame)
        
        # Update parking spaces
        state_changes = self.space_manager.update_all(
            vehicle_bboxes, vehicle_centroids, vehicle_classes, timestamp
        )
        
        # Log state changes
        for change in state_changes:
            space = next(s for s in self.space_manager.spaces 
                        if s.space_id == change['space_id'])
            self.logger.log_state_change(
                change['space_id'],
                change['old_state'],
                change['new_state'],
                change['timestamp'],
                vehicle_class=None,  # Could match vehicle to space if needed
                confidence=None,
                occupancy_duration=space.occupancy_duration
            )
        
        # Log metrics
        empty, occupied = self.space_manager.get_counts()
        self.logger.log_metrics(timestamp, empty, occupied)
        
        # Visualize
        annotated_frame = self.visualizer.visualize_frame(
            frame, self.space_manager, vehicle_bboxes, self.fps, timestamp
        )
        
        return annotated_frame
    
    def process_video_file(self, video_path: str, output_path: Optional[str] = None,
                          show_display: bool = True):
        """
        Process a video file.
        
        Args:
            video_path: Path to input video file
            output_path: Optional path to save output video
            show_display: Whether to show live display window
        """
        print(f"Opening video: {video_path}")
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            raise ValueError(f"Could not open video: {video_path}")
        
        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        print(f"Video properties: {width}x{height} @ {fps} FPS, {total_frames} frames")
        
        # Setup video writer if output path provided
        writer = None
        if output_path:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
            print(f"Output video will be saved to: {output_path}")
        
        frame_idx = 0
        start_time = time.time()
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                frame_idx += 1
                
                # Calculate timestamp
                timestamp = datetime.now()
                if fps > 0:
                    frame_time = frame_idx / fps
                    # Could use video timestamp if available
                
                # Process frame
                processed_frame = self.process_frame(frame, timestamp)
                
                # Write to output video
                if writer:
                    writer.write(processed_frame)
                
                # Display
                if show_display:
                    cv2.imshow('Parking Lot Monitor', processed_frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        print("Stopped by user")
                        break
                
                # FPS calculation
                self.frame_count += 1
                current_time = time.time()
                if current_time - self.last_fps_time >= 1.0:
                    self.fps = self.frame_count / (current_time - self.last_fps_time)
                    self.frame_count = 0
                    self.last_fps_time = current_time
                    print(f"Processing: {frame_idx}/{total_frames} frames "
                          f"({self.fps:.1f} FPS)")
                
                # Frame rate limiting
                if self.fps_limit > 0:
                    time.sleep(max(0, self.frame_time - (time.time() - start_time)))
                    start_time = time.time()
        
        finally:
            cap.release()
            if writer:
                writer.release()
            if show_display:
                cv2.destroyAllWindows()
            
            print(f"Processed {frame_idx} frames")
            print(f"Final statistics:")
            empty, occupied = self.space_manager.get_counts()
            print(f"  Empty: {empty}, Occupied: {occupied}")
    
    def process_webcam(self, camera_index: int = 0, show_display: bool = True):
        """
        Process live webcam feed.
        
        Args:
            camera_index: Camera device index
            show_display: Whether to show live display window
        """
        print(f"Opening camera {camera_index}")
        cap = cv2.VideoCapture(camera_index)
        
        if not cap.isOpened():
            raise ValueError(f"Could not open camera {camera_index}")
        
        # Set camera properties
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
        
        print("Camera opened. Press 'q' to quit.")
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    print("Failed to read frame")
                    break
                
                timestamp = datetime.now()
                
                # Process frame
                processed_frame = self.process_frame(frame, timestamp)
                
                # Display
                if show_display:
                    cv2.imshow('Parking Lot Monitor', processed_frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        print("Stopped by user")
                        break
                
                # FPS calculation
                self.frame_count += 1
                current_time = time.time()
                if current_time - self.last_fps_time >= 1.0:
                    self.fps = self.frame_count / (current_time - self.last_fps_time)
                    self.frame_count = 0
                    self.last_fps_time = current_time
                    if self.frame_count % 30 == 0:  # Print every 30 frames
                        empty, occupied = self.space_manager.get_counts()
                        print(f"FPS: {self.fps:.1f} | "
                              f"Empty: {empty}, Occupied: {occupied}")
        
        finally:
            cap.release()
            if show_display:
                cv2.destroyAllWindows()
    
    def process_rtsp(self, rtsp_url: str, show_display: bool = True):
        """
        Process RTSP stream.
        
        Args:
            rtsp_url: RTSP stream URL
            show_display: Whether to show live display window
        """
        print(f"Connecting to RTSP stream: {rtsp_url}")
        cap = cv2.VideoCapture(rtsp_url)
        
        if not cap.isOpened():
            raise ValueError(f"Could not open RTSP stream: {rtsp_url}")
        
        print("RTSP stream connected. Press 'q' to quit.")
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    print("Failed to read frame from stream")
                    time.sleep(0.1)
                    continue
                
                timestamp = datetime.now()
                
                # Process frame
                processed_frame = self.process_frame(frame, timestamp)
                
                # Display
                if show_display:
                    cv2.imshow('Parking Lot Monitor', processed_frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        print("Stopped by user")
                        break
                
                # FPS calculation
                self.frame_count += 1
                current_time = time.time()
                if current_time - self.last_fps_time >= 1.0:
                    self.fps = self.frame_count / (current_time - self.last_fps_time)
                    self.frame_count = 0
                    self.last_fps_time = current_time
        
        finally:
            cap.release()
            if show_display:
                cv2.destroyAllWindows()
    
    def export_results(self, output_dir: str = "output"):
        """
        Export logging results and metrics.
        
        Args:
            output_dir: Output directory for exports
        """
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Export JSON metrics
        json_path = os.path.join(output_dir, f"metrics_{timestamp_str}.json")
        self.logger.export_metrics_json(json_path)
        
        # Export CSV metrics
        csv_path = os.path.join(output_dir, f"metrics_{timestamp_str}.csv")
        self.logger.export_metrics_csv(csv_path)
        
        print(f"Results exported to {output_dir}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Parking Lot Monitoring System - Real-time vehicle detection and occupancy tracking"
    )
    
    # Input options
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument('--video', type=str, help='Path to input video file')
    input_group.add_argument('--webcam', type=int, nargs='?', const=0, 
                            help='Use webcam (optional camera index)')
    input_group.add_argument('--rtsp', type=str, help='RTSP stream URL')
    
    # Configuration
    parser.add_argument('--config', type=str, required=True,
                       help='Path to parking spaces configuration JSON file')
    parser.add_argument('--output', type=str, default=None,
                       help='Path to save output video (for video input only)')
    parser.add_argument('--log', type=str, default=None,
                       help='Path to CSV log file for state changes')
    parser.add_argument('--export-dir', type=str, default='output',
                       help='Directory for exporting metrics (default: output)')
    
    # Detection parameters
    parser.add_argument('--confidence', type=float, default=0.5,
                       help='Vehicle detection confidence threshold (0-1, default: 0.5)')
    parser.add_argument('--min-occupancy', type=float, default=0.2,
                       help='Minimum occupancy ratio for space classification (0-1, default: 0.2 = 20%)')
    parser.add_argument('--fps-limit', type=int, default=30,
                       help='Maximum processing FPS (0 = unlimited, default: 30)')
    
    # Detector options
    parser.add_argument('--simple-detector', action='store_true',
                       help='Use simple background subtraction instead of YOLO')
    parser.add_argument('--device', type=str, default='cpu',
                       choices=['cpu', 'cuda', 'mps'],
                       help='Device for YOLO inference (default: cpu)')
    
    # Display options
    parser.add_argument('--no-display', action='store_true',
                       help='Disable live display window')
    
    # Web server options
    parser.add_argument('--web-server', action='store_true',
                       help='Start web server for remote monitoring')
    parser.add_argument('--web-host', type=str, default='0.0.0.0',
                       help='Web server host (default: 0.0.0.0)')
    parser.add_argument('--web-port', type=int, default=5000,
                       help='Web server port (default: 5000)')
    
    args = parser.parse_args()
    
    # Initialize analyzer
    try:
        analyzer = ParkingAnalyzer(
            config_path=args.config,
            confidence_threshold=args.confidence,
            min_occupancy_ratio=args.min_occupancy,
            fps_limit=args.fps_limit,
            use_simple_detector=args.simple_detector,
            device=args.device
        )
        
        # Setup logger if log file specified
        if args.log:
            analyzer.logger = ParkingLogger(args.log)
        
        # Start web server if requested
        web_server_thread = None
        if args.web_server:
            try:
                from web_server import init_web_server, start_web_server_thread
                init_web_server(analyzer.space_manager, analyzer.logger)
                web_server_thread = start_web_server_thread(args.web_host, args.web_port)
                print(f"Web server started at http://{args.web_host}:{args.web_port}")
            except ImportError:
                print("Warning: Flask not available. Web server disabled.")
                print("Install Flask with: pip install flask")
        
        # Process input
        show_display = not args.no_display
        
        if args.video:
            analyzer.process_video_file(args.video, args.output, show_display)
        elif args.webcam is not None:
            analyzer.process_webcam(args.webcam, show_display)
        elif args.rtsp:
            analyzer.process_rtsp(args.rtsp, show_display)
        
        # Export results
        analyzer.export_results(args.export_dir)
        
        # Keep web server running if started
        if web_server_thread and web_server_thread.is_alive():
            print(f"\nWeb server running at http://{args.web_host}:{args.web_port}")
            print("Press Ctrl+C to stop...")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\nShutting down...")
        
        print("Analysis complete!")
        
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

