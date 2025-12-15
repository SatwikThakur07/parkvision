"""
Vehicle Detection Module
Wrapper for YOLOv8 object detection with filtering for vehicles only.
"""

import cv2
import numpy as np
from typing import List, Tuple, Optional
try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    print("Warning: YOLOv8 not available. Install with: pip install ultralytics")


class VehicleDetector:
    """Vehicle detection using YOLOv8 model"""
    
    # Vehicle class IDs in COCO dataset
    VEHICLE_CLASSES = {
        'car': 2,
        'motorcycle': 3,
        'bus': 5,
        'truck': 7
    }
    
    def __init__(self, model_path: Optional[str] = None, 
                 confidence_threshold: float = 0.5,
                 device: str = 'cpu'):
        """
        Initialize the vehicle detector.
        
        Args:
            model_path: Path to YOLOv8 model file (None uses default YOLOv8n)
            confidence_threshold: Minimum confidence for detections (0-1)
            device: Device to run on ('cpu', 'cuda', 'mps')
        """
        if not YOLO_AVAILABLE:
            raise ImportError("YOLOv8 is required. Install with: pip install ultralytics")
        
        self.confidence_threshold = confidence_threshold
        self.device = device
        
        # Load YOLOv8 model
        if model_path:
            self.model = YOLO(model_path)
        else:
            # Use default YOLOv8n (nano) for speed
            self.model = YOLO('yolov8n.pt')
        
        # Get class IDs for vehicles
        self.vehicle_class_ids = list(self.VEHICLE_CLASSES.values())
    
    def detect(self, frame: np.ndarray) -> Tuple[List[Tuple[int, int, int, int]], 
                                                   List[Tuple[int, int]], 
                                                   List[str], 
                                                   List[float]]:
        """
        Detect vehicles in a frame.
        
        Args:
            frame: Input image frame (BGR format)
            
        Returns:
            Tuple of (bounding_boxes, centroids, class_names, confidences)
            - bounding_boxes: List of (x1, y1, x2, y2)
            - centroids: List of (x, y)
            - class_names: List of class names
            - confidences: List of confidence scores
        """
        # Run YOLOv8 inference
        results = self.model(frame, conf=self.confidence_threshold, device=self.device, verbose=False)
        
        bounding_boxes = []
        centroids = []
        class_names = []
        confidences = []
        
        # Parse results
        for result in results:
            boxes = result.boxes
            for i in range(len(boxes)):
                # Get box coordinates
                box = boxes.xyxy[i].cpu().numpy()
                x1, y1, x2, y2 = box.astype(int)
                
                # Get class ID and confidence
                cls_id = int(boxes.cls[i].cpu().numpy())
                conf = float(boxes.conf[i].cpu().numpy())
                
                # Filter for vehicles only
                if cls_id in self.vehicle_class_ids:
                    # Get class name
                    class_name = result.names[cls_id]
                    
                    # Calculate centroid
                    centroid = ((x1 + x2) // 2, (y1 + y2) // 2)
                    
                    bounding_boxes.append((x1, y1, x2, y2))
                    centroids.append(centroid)
                    class_names.append(class_name)
                    confidences.append(conf)
        
        return bounding_boxes, centroids, class_names, confidences
    
    def draw_detections(self, frame: np.ndarray, 
                       bounding_boxes: List[Tuple[int, int, int, int]],
                       class_names: List[str],
                       confidences: List[float]) -> np.ndarray:
        """
        Draw vehicle detections on frame.
        
        Args:
            frame: Input frame
            bounding_boxes: List of bounding boxes
            class_names: List of class names
            confidences: List of confidence scores
            
        Returns:
            Annotated frame
        """
        annotated_frame = frame.copy()
        
        for (x1, y1, x2, y2), class_name, conf in zip(bounding_boxes, class_names, confidences):
            # Draw bounding box
            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (255, 0, 0), 2)
            
            # Draw label
            label = f"{class_name} {conf:.2f}"
            label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
            cv2.rectangle(annotated_frame, (x1, y1 - label_size[1] - 10),
                         (x1 + label_size[0], y1), (255, 0, 0), -1)
            cv2.putText(annotated_frame, label, (x1, y1 - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
        
        return annotated_frame


class SimpleVehicleDetector:
    """
    Fallback simple detector using background subtraction and contours.
    Use this if YOLOv8 is not available or for testing.
    """
    
    def __init__(self, confidence_threshold: float = 0.5):
        self.confidence_threshold = confidence_threshold
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=500, varThreshold=50, detectShadows=True
        )
        self.min_area = 500  # Minimum contour area to consider as vehicle
    
    def detect(self, frame: np.ndarray) -> Tuple[List[Tuple[int, int, int, int]], 
                                                   List[Tuple[int, int]], 
                                                   List[str], 
                                                   List[float]]:
        """Simple detection using background subtraction"""
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Apply background subtraction
        fg_mask = self.bg_subtractor.apply(gray)
        
        # Morphological operations to reduce noise
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, kernel)
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel)
        
        # Find contours
        contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        bounding_boxes = []
        centroids = []
        class_names = []
        confidences = []
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > self.min_area:
                x, y, w, h = cv2.boundingRect(contour)
                x1, y1, x2, y2 = x, y, x + w, y + h
                
                # Calculate centroid
                M = cv2.moments(contour)
                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                    
                    bounding_boxes.append((x1, y1, x2, y2))
                    centroids.append((cx, cy))
                    class_names.append("vehicle")
                    confidences.append(0.7)  # Fixed confidence for simple detector
        
        return bounding_boxes, centroids, class_names, confidences
    
    def draw_detections(self, frame: np.ndarray, 
                       bounding_boxes: List[Tuple[int, int, int, int]],
                       class_names: List[str],
                       confidences: List[float]) -> np.ndarray:
        """Draw detections on frame"""
        annotated_frame = frame.copy()
        for (x1, y1, x2, y2), _, _ in zip(bounding_boxes, class_names, confidences):
            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (255, 0, 0), 2)
        return annotated_frame

