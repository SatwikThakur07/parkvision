"""
Visualization Module
Handles real-time video display with parking space overlays and statistics.
"""

import cv2
import numpy as np
from typing import List, Tuple, Optional
from parking_space import ParkingSpace, ParkingSpaceManager
from datetime import datetime


class Visualizer:
    """Handles visualization of parking spaces and statistics"""
    
    def __init__(self, show_detections: bool = True, show_ids: bool = True):
        """
        Initialize the visualizer.
        
        Args:
            show_detections: Whether to show vehicle detection bounding boxes
            show_ids: Whether to show parking space IDs
        """
        self.show_detections = show_detections
        self.show_ids = show_ids
    
    def draw_spaces(self, frame: np.ndarray, space_manager: ParkingSpaceManager) -> np.ndarray:
        """
        Draw parking spaces on frame.
        
        Args:
            frame: Input frame
            space_manager: ParkingSpaceManager instance
            
        Returns:
            Annotated frame
        """
        annotated_frame = frame.copy()
        
        for space in space_manager.spaces:
            # Draw polygon
            color = space.get_color()
            thickness = 2
            
            # Draw filled polygon with transparency
            overlay = annotated_frame.copy()
            cv2.fillPoly(overlay, [space.polygon], color)
            cv2.addWeighted(overlay, 0.3, annotated_frame, 0.7, 0, annotated_frame)
            
            # Draw polygon outline
            cv2.polylines(annotated_frame, [space.polygon], True, color, thickness)
            
            # Draw space ID
            if self.show_ids:
                centroid = space.get_centroid()
                if centroid[0] > 0 and centroid[1] > 0:
                    cv2.putText(annotated_frame, f"#{space.space_id}", 
                               (centroid[0] - 15, centroid[1]),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
                    cv2.putText(annotated_frame, f"#{space.space_id}", 
                               (centroid[0] - 15, centroid[1]),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
        
        return annotated_frame
    
    def draw_statistics(self, frame: np.ndarray, space_manager: ParkingSpaceManager,
                       fps: float = 0.0, timestamp: Optional[datetime] = None) -> np.ndarray:
        """
        Draw statistics overlay on frame.
        
        Args:
            frame: Input frame
            space_manager: ParkingSpaceManager instance
            fps: Current FPS
            timestamp: Current timestamp
            
        Returns:
            Annotated frame
        """
        annotated_frame = frame.copy()
        height, width = frame.shape[:2]
        
        # Get counts
        empty, occupied = space_manager.get_counts()
        total = space_manager.total_spaces
        occupancy_rate = space_manager.get_occupancy_rate()
        
        # Create overlay panel
        panel_height = 150
        overlay = np.zeros((panel_height, width, 3), dtype=np.uint8)
        overlay[:] = (0, 0, 0)  # Black background
        
        # Add semi-transparent overlay
        y_offset = 10
        cv2.addWeighted(annotated_frame[y_offset:y_offset+panel_height, :], 0.3,
                       overlay, 0.7, 0, overlay)
        annotated_frame[y_offset:y_offset+panel_height, :] = overlay
        
        # Draw statistics text
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.7
        thickness = 2
        color = (255, 255, 255)
        
        y_pos = 40
        line_height = 30
        
        # Title
        cv2.putText(annotated_frame, "Parking Lot Status", (20, y_pos),
                   font, 1.0, color, thickness)
        y_pos += line_height + 10
        
        # Counts
        status_text = f"Empty: {empty}/{total}  |  Occupied: {occupied}/{total}"
        cv2.putText(annotated_frame, status_text, (20, y_pos),
                   font, font_scale, (0, 255, 0), thickness)
        y_pos += line_height
        
        # Occupancy rate
        rate_text = f"Occupancy Rate: {occupancy_rate*100:.1f}%"
        cv2.putText(annotated_frame, rate_text, (20, y_pos),
                   font, font_scale, color, thickness)
        y_pos += line_height
        
        # FPS and timestamp
        info_text = f"FPS: {fps:.1f}"
        if timestamp:
            time_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
            info_text += f"  |  {time_str}"
        cv2.putText(annotated_frame, info_text, (20, y_pos),
                   font, 0.5, (200, 200, 200), 1)
        
        return annotated_frame
    
    def draw_legend(self, frame: np.ndarray) -> np.ndarray:
        """
        Draw color legend for parking space states.
        
        Args:
            frame: Input frame
            
        Returns:
            Annotated frame
        """
        annotated_frame = frame.copy()
        height, width = frame.shape[:2]
        
        # Legend position (bottom right)
        legend_x = width - 200
        legend_y = height - 100
        
        # Draw legend background
        cv2.rectangle(annotated_frame, (legend_x - 10, legend_y - 10),
                     (width - 10, height - 10), (0, 0, 0), -1)
        cv2.rectangle(annotated_frame, (legend_x - 10, legend_y - 10),
                     (width - 10, height - 10), (255, 255, 255), 2)
        
        # Draw legend items
        font = cv2.FONT_HERSHEY_SIMPLEX
        y_offset = legend_y
        
        # Empty (green)
        cv2.rectangle(annotated_frame, (legend_x, y_offset),
                     (legend_x + 20, y_offset + 15), (0, 255, 0), -1)
        cv2.putText(annotated_frame, "Empty", (legend_x + 30, y_offset + 12),
                   font, 0.5, (255, 255, 255), 1)
        y_offset += 25
        
        # Occupied (red)
        cv2.rectangle(annotated_frame, (legend_x, y_offset),
                     (legend_x + 20, y_offset + 15), (0, 0, 255), -1)
        cv2.putText(annotated_frame, "Occupied", (legend_x + 30, y_offset + 12),
                   font, 0.5, (255, 255, 255), 1)
        
        return annotated_frame
    
    def visualize_frame(self, frame: np.ndarray, space_manager: ParkingSpaceManager,
                       vehicle_bboxes: Optional[List[Tuple[int, int, int, int]]] = None,
                       fps: float = 0.0, timestamp: Optional[datetime] = None) -> np.ndarray:
        """
        Create complete visualization of frame with all overlays.
        
        Args:
            frame: Input frame
            space_manager: ParkingSpaceManager instance
            vehicle_bboxes: Optional list of vehicle bounding boxes to draw
            fps: Current FPS
            timestamp: Current timestamp
            
        Returns:
            Fully annotated frame
        """
        # Draw parking spaces
        annotated = self.draw_spaces(frame, space_manager)
        
        # Draw vehicle detections if enabled
        if self.show_detections and vehicle_bboxes:
            for x1, y1, x2, y2 in vehicle_bboxes:
                cv2.rectangle(annotated, (x1, y1), (x2, y2), (255, 0, 0), 2)
        
        # Draw statistics
        annotated = self.draw_statistics(annotated, space_manager, fps, timestamp)
        
        # Draw legend
        annotated = self.draw_legend(annotated)
        
        return annotated

