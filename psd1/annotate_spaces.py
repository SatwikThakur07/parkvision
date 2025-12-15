#!/usr/bin/env python3
"""
Parking Space Annotation Tool
Interactive tool for drawing parking space polygons on a video frame or image.
"""

import cv2
import numpy as np
import json
import argparse
import os
from typing import List, Tuple
from config_manager import ConfigManager


class SpaceAnnotator:
    """Interactive parking space annotation tool"""
    
    def __init__(self, image_path: str):
        """
        Initialize the annotator.
        
        Args:
            image_path: Path to image or video file
        """
        self.image_path = image_path
        self.spaces = []
        self.current_space_id = 1
        self.current_polygon = []
        self.drawing = False
        self.image = None
        self.display_image = None
        
        # Load image or first frame of video
        if image_path.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
            cap = cv2.VideoCapture(image_path)
            ret, frame = cap.read()
            if ret:
                self.image = frame
                cap.release()
            else:
                raise ValueError(f"Could not read video: {image_path}")
        else:
            self.image = cv2.imread(image_path)
            if self.image is None:
                raise ValueError(f"Could not read image: {image_path}")
        
        self.display_image = self.image.copy()
        self.window_name = "Parking Space Annotator"
        
    def mouse_callback(self, event, x, y, flags, param):
        """Mouse callback for drawing polygons"""
        if event == cv2.EVENT_LBUTTONDOWN:
            self.drawing = True
            self.current_polygon.append((x, y))
            
        elif event == cv2.EVENT_MOUSEMOVE and self.drawing:
            # Draw temporary line
            temp_image = self.display_image.copy()
            if len(self.current_polygon) > 0:
                pts = np.array(self.current_polygon + [(x, y)], dtype=np.int32)
                cv2.polylines(temp_image, [pts], False, (0, 255, 0), 2)
            cv2.imshow(self.window_name, temp_image)
            
        elif event == cv2.EVENT_LBUTTONUP:
            self.drawing = False
    
    def finish_polygon(self):
        """Finish current polygon and add to spaces"""
        if len(self.current_polygon) >= 3:
            space = {
                'id': self.current_space_id,
                'polygon': self.current_polygon.copy(),
                'min_occupancy_ratio': 0.3
            }
            self.spaces.append(space)
            self.current_space_id += 1
            self.current_polygon = []
            self.redraw()
            print(f"Added space #{space['id']} with {len(space['polygon'])} points")
        else:
            print("Polygon needs at least 3 points")
            self.current_polygon = []
            self.redraw()
    
    def redraw(self):
        """Redraw the image with all annotated spaces"""
        self.display_image = self.image.copy()
        
        # Draw existing spaces
        for space in self.spaces:
            pts = np.array(space['polygon'], dtype=np.int32)
            cv2.fillPoly(self.display_image, [pts], (0, 255, 0, 100))
            cv2.polylines(self.display_image, [pts], True, (0, 255, 0), 2)
            
            # Draw space ID
            if len(pts) > 0:
                centroid = np.mean(pts, axis=0).astype(int)
                cv2.putText(self.display_image, f"#{space['id']}",
                           tuple(centroid), cv2.FONT_HERSHEY_SIMPLEX,
                           0.7, (255, 255, 255), 2)
        
        # Draw current polygon being drawn
        if len(self.current_polygon) > 1:
            pts = np.array(self.current_polygon, dtype=np.int32)
            cv2.polylines(self.display_image, [pts], False, (255, 0, 0), 2)
            for pt in self.current_polygon:
                cv2.circle(self.display_image, pt, 5, (255, 0, 0), -1)
        
        cv2.imshow(self.window_name, self.display_image)
    
    def delete_last_space(self):
        """Delete the last added space"""
        if self.spaces:
            deleted = self.spaces.pop()
            self.current_space_id = deleted['id']
            print(f"Deleted space #{deleted['id']}")
            self.redraw()
    
    def annotate(self):
        """Run the annotation interface"""
        cv2.namedWindow(self.window_name)
        cv2.setMouseCallback(self.window_name, self.mouse_callback)
        
        print("\n=== Parking Space Annotator ===")
        print("Instructions:")
        print("  - Click to add points to polygon")
        print("  - Press ENTER to finish current polygon")
        print("  - Press 'd' to delete last space")
        print("  - Press 's' to save and exit")
        print("  - Press 'q' to quit without saving")
        print("===============================\n")
        
        self.redraw()
        
        while True:
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('\n') or key == ord('\r'):  # Enter
                self.finish_polygon()
            elif key == ord('d'):
                self.delete_last_space()
            elif key == ord('s'):
                break
            elif key == ord('q'):
                self.spaces = []
                break
        
        cv2.destroyAllWindows()
        return self.spaces
    
    def save_config(self, output_path: str):
        """Save annotation to JSON config file"""
        config = {
            'default_min_occupancy_ratio': 0.3,
            'spaces': self.spaces
        }
        
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.',
                   exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"\nSaved {len(self.spaces)} parking spaces to: {output_path}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Interactive tool for annotating parking spaces"
    )
    parser.add_argument('input', type=str,
                       help='Path to image or video file')
    parser.add_argument('--output', type=str, default='spaces.json',
                       help='Output JSON config file (default: spaces.json)')
    
    args = parser.parse_args()
    
    try:
        annotator = SpaceAnnotator(args.input)
        spaces = annotator.annotate()
        
        if spaces:
            annotator.save_config(args.output)
            print(f"\nAnnotation complete! {len(spaces)} spaces saved.")
        else:
            print("\nNo spaces saved.")
    
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()

