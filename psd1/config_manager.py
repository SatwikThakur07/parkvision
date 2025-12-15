"""
Configuration Management Module
Handles loading and saving parking space configurations from JSON files.
"""

import json
import os
from typing import List, Dict, Any
from parking_space import ParkingSpace


class ConfigManager:
    """Manages parking space configuration files"""
    
    @staticmethod
    def load_spaces(config_path: str) -> List[ParkingSpace]:
        """
        Load parking spaces from JSON configuration file.
        
        Args:
            config_path: Path to JSON configuration file
            
        Returns:
            List of ParkingSpace objects
            
        JSON Format:
        {
            "spaces": [
                {
                    "id": 1,
                    "polygon": [[x1, y1], [x2, y2], [x3, y3], [x4, y4]],
                    "min_occupancy_ratio": 0.3
                },
                ...
            ],
            "default_min_occupancy_ratio": 0.3
        }
        """
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        spaces = []
        default_ratio = config.get('default_min_occupancy_ratio', 0.2)
        
        for space_config in config.get('spaces', []):
            space_id = space_config['id']
            polygon_points = space_config['polygon']
            # Convert to list of tuples
            polygon = [(int(p[0]), int(p[1])) for p in polygon_points]
            min_ratio = space_config.get('min_occupancy_ratio', default_ratio)
            
            space = ParkingSpace(space_id, polygon, min_ratio)
            spaces.append(space)
        
        return spaces
    
    @staticmethod
    def save_spaces(spaces: List[ParkingSpace], config_path: str,
                   default_min_occupancy_ratio: float = 0.2):
        """
        Save parking spaces to JSON configuration file.
        
        Args:
            spaces: List of ParkingSpace objects
            config_path: Path to save JSON configuration file
            default_min_occupancy_ratio: Default occupancy ratio
        """
        config = {
            'default_min_occupancy_ratio': default_min_occupancy_ratio,
            'spaces': []
        }
        
        for space in spaces:
            space_config = {
                'id': space.space_id,
                'polygon': space.polygon.tolist(),
                'min_occupancy_ratio': space.min_occupancy_ratio
            }
            config['spaces'].append(space_config)
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(config_path) if os.path.dirname(config_path) else '.', 
                   exist_ok=True)
        
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
    
    @staticmethod
    def create_sample_config(config_path: str, num_spaces: int = 10,
                            image_width: int = 1920, image_height: int = 1080,
                            default_min_occupancy_ratio: float = 0.2):
        """
        Create a sample configuration file with grid-based parking spaces.
        Useful for testing or as a starting point.
        
        Args:
            config_path: Path to save sample configuration
            num_spaces: Number of spaces to create (will create a grid)
            image_width: Width of the video frame
            image_height: Height of the video frame
        """
        import math
        
        # Calculate grid dimensions
        cols = int(math.ceil(math.sqrt(num_spaces)))
        rows = int(math.ceil(num_spaces / cols))
        
        space_width = image_width // (cols + 1)
        space_height = image_height // (rows + 1)
        
        spaces = []
        space_id = 1
        
        for row in range(rows):
            for col in range(cols):
                if space_id > num_spaces:
                    break
                
                x1 = col * space_width + space_width // 4
                y1 = row * space_height + space_height // 4
                x2 = (col + 1) * space_width - space_width // 4
                y2 = (row + 1) * space_height - space_height // 4
                
                polygon = [
                    [x1, y1],
                    [x2, y1],
                    [x2, y2],
                    [x1, y2]
                ]
                
                spaces.append({
                    'id': space_id,
                    'polygon': polygon,
                    'min_occupancy_ratio': default_min_occupancy_ratio
                })
                space_id += 1
        
        config = {
            'default_min_occupancy_ratio': default_min_occupancy_ratio,
            'spaces': spaces
        }
        
        os.makedirs(os.path.dirname(config_path) if os.path.dirname(config_path) else '.', 
                   exist_ok=True)
        
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"Sample configuration created: {config_path}")
        print(f"Created {len(spaces)} parking spaces in a {rows}x{cols} grid")

