"""
Parking Space Management Module
Handles individual parking space detection, state tracking, and occupancy classification.
"""

import numpy as np
import cv2
from typing import List, Tuple, Optional
from datetime import datetime
from enum import Enum


class SpaceState(Enum):
    """Parking space occupancy states"""
    EMPTY = "empty"
    OCCUPIED = "occupied"
    UNKNOWN = "unknown"


class ParkingSpace:
    """Represents a single parking space with polygon boundaries and state tracking"""
    
    def __init__(self, space_id: int, polygon: List[Tuple[int, int]], 
                 min_occupancy_ratio: float = 0.2):
        """
        Initialize a parking space.
        
        Args:
            space_id: Unique identifier for the space
            polygon: List of (x, y) coordinates defining the space boundary
            min_occupancy_ratio: Minimum area ratio (0-1) to consider space occupied (0.2 = 20%)
        """
        self.space_id = space_id
        self.polygon = np.array(polygon, dtype=np.int32)
        self.min_occupancy_ratio = min_occupancy_ratio
        self.state = SpaceState.UNKNOWN
        self.previous_state = SpaceState.UNKNOWN
        self.state_history = []  # List of (timestamp, state) tuples
        self.last_change_time = None
        self.occupancy_duration = 0.0
        self.vehicle_count = 0
        self.confidence_smoothing = []  # For temporal smoothing
        self.smoothing_window = 5  # Number of frames for state persistence
        
    def get_centroid(self) -> Tuple[float, float]:
        """Calculate the centroid of the parking space polygon"""
        M = cv2.moments(self.polygon)
        if M["m00"] != 0:
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])
            return (cx, cy)
        return (0, 0)
    
    def get_area(self) -> float:
        """Calculate the area of the parking space polygon"""
        return cv2.contourArea(self.polygon)
    
    def point_inside(self, point: Tuple[int, int]) -> bool:
        """Check if a point is inside the parking space polygon"""
        # Convert point to tuple of floats for OpenCV compatibility
        pt = (float(point[0]), float(point[1]))
        return cv2.pointPolygonTest(self.polygon, pt, False) >= 0
    
    def bbox_intersection_ratio(self, bbox: Tuple[int, int, int, int]) -> float:
        """
        Calculate the intersection ratio between a bounding box and the parking space.
        
        Args:
            bbox: (x1, y1, x2, y2) bounding box coordinates
            
        Returns:
            Ratio of intersection area to parking space area (0-1)
        """
        x1, y1, x2, y2 = bbox
        bbox_polygon = np.array([
            [x1, y1],
            [x2, y1],
            [x2, y2],
            [x1, y2]
        ], dtype=np.int32)
        
        # Calculate intersection using OpenCV
        space_area = self.get_area()
        if space_area == 0:
            return 0.0
        
        # Create mask for parking space
        mask_space = np.zeros((max(y2, self.polygon[:, 1].max()) + 10,
                              max(x2, self.polygon[:, 0].max()) + 10), dtype=np.uint8)
        cv2.fillPoly(mask_space, [self.polygon], 255)
        
        # Create mask for bounding box
        mask_bbox = np.zeros_like(mask_space)
        cv2.fillPoly(mask_bbox, [bbox_polygon], 255)
        
        # Calculate intersection
        intersection = cv2.bitwise_and(mask_space, mask_bbox)
        intersection_area = np.sum(intersection > 0)
        
        return intersection_area / space_area
    
    def check_occupancy(self, vehicle_bboxes: List[Tuple[int, int, int, int]], 
                       vehicle_centroids: List[Tuple[int, int]]) -> bool:
        """
        Check if the parking space is occupied based on vehicle detections.
        Space is considered occupied if ANY part of a vehicle overlaps with it.
        
        Args:
            vehicle_bboxes: List of (x1, y1, x2, y2) bounding boxes
            vehicle_centroids: List of (x, y) centroid coordinates
            
        Returns:
            True if space is occupied, False otherwise
        """
        self.vehicle_count = 0
        max_intersection = 0.0
        
        for bbox, centroid in zip(vehicle_bboxes, vehicle_centroids):
            # Check if there's any overlap between vehicle and space
            # Either centroid is inside OR bbox intersects with space
            centroid_inside = self.point_inside(centroid)
            intersection_ratio = self.bbox_intersection_ratio(bbox)
            
            # If any part overlaps (intersection > 0) or centroid is inside
            if intersection_ratio > 0.0 or centroid_inside:
                max_intersection = max(max_intersection, intersection_ratio)
                # With min_occupancy_ratio = 0.0, any overlap counts
                if intersection_ratio > self.min_occupancy_ratio:
                    self.vehicle_count += 1
        
        # Use temporal smoothing to handle flickering
        # With 0.0 threshold, any detected overlap means occupied
        is_occupied = max_intersection > 0.0 if self.min_occupancy_ratio == 0.0 else max_intersection >= self.min_occupancy_ratio
        self.confidence_smoothing.append(1.0 if is_occupied else 0.0)
        
        # Keep only recent frames
        if len(self.confidence_smoothing) > self.smoothing_window:
            self.confidence_smoothing.pop(0)
        
        # Require majority of recent frames to agree
        if len(self.confidence_smoothing) >= 3:
            avg_confidence = np.mean(self.confidence_smoothing)
            is_occupied = avg_confidence >= 0.5
        
        return is_occupied
    
    def update_state(self, is_occupied: bool, timestamp: Optional[datetime] = None):
        """
        Update the parking space state and log changes.
        
        Args:
            is_occupied: Whether the space is currently occupied
            timestamp: Current timestamp (defaults to now)
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        new_state = SpaceState.OCCUPIED if is_occupied else SpaceState.EMPTY
        self.previous_state = self.state
        self.state = new_state
        
        # Log state change
        if self.previous_state != self.state and self.previous_state != SpaceState.UNKNOWN:
            self.last_change_time = timestamp
            self.state_history.append((timestamp, self.state))
            
            # Calculate occupancy duration if transitioning to empty
            if self.state == SpaceState.EMPTY and self.previous_state == SpaceState.OCCUPIED:
                if len(self.state_history) >= 2:
                    prev_timestamp, _ = self.state_history[-2]
                    duration = (timestamp - prev_timestamp).total_seconds()
                    self.occupancy_duration = duration
    
    def get_state_string(self) -> str:
        """Get human-readable state string"""
        return self.state.value
    
    def get_color(self) -> Tuple[int, int, int]:
        """Get color for visualization (green=empty, red=occupied)"""
        if self.state == SpaceState.OCCUPIED:
            return (0, 0, 255)  # Red
        elif self.state == SpaceState.EMPTY:
            return (0, 255, 0)  # Green
        else:
            return (128, 128, 128)  # Gray


class ParkingSpaceManager:
    """Manages multiple parking spaces and their states"""
    
    def __init__(self, spaces: List[ParkingSpace]):
        """
        Initialize the parking space manager.
        
        Args:
            spaces: List of ParkingSpace objects
        """
        self.spaces = spaces
        self.total_spaces = len(spaces)
    
    def update_all(self, vehicle_bboxes: List[Tuple[int, int, int, int]],
                   vehicle_centroids: List[Tuple[int, int]],
                   vehicle_classes: List[str],
                   timestamp: Optional[datetime] = None):
        """
        Update all parking spaces based on current vehicle detections.
        
        Args:
            vehicle_bboxes: List of vehicle bounding boxes
            vehicle_centroids: List of vehicle centroids
            vehicle_classes: List of vehicle class names
            timestamp: Current timestamp
        """
        state_changes = []
        
        for space in self.spaces:
            is_occupied = space.check_occupancy(vehicle_bboxes, vehicle_centroids)
            old_state = space.state
            space.update_state(is_occupied, timestamp)
            
            # Track state changes
            if old_state != space.state and old_state != SpaceState.UNKNOWN:
                state_changes.append({
                    'space_id': space.space_id,
                    'old_state': old_state.value,
                    'new_state': space.state.value,
                    'timestamp': timestamp or datetime.now()
                })
        
        return state_changes
    
    def get_counts(self) -> Tuple[int, int]:
        """Get current empty and occupied counts"""
        empty = sum(1 for s in self.spaces if s.state == SpaceState.EMPTY)
        occupied = sum(1 for s in self.spaces if s.state == SpaceState.OCCUPIED)
        return empty, occupied
    
    def get_occupancy_rate(self) -> float:
        """Get current occupancy rate (0-1)"""
        if self.total_spaces == 0:
            return 0.0
        _, occupied = self.get_counts()
        return occupied / self.total_spaces

