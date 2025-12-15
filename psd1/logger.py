"""
Logging and Metrics Module
Handles state change logging, metrics computation, and data export.
"""

import csv
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np


class ParkingLogger:
    """Logs parking space state changes and computes metrics"""
    
    def __init__(self, log_file: Optional[str] = None):
        """
        Initialize the logger.
        
        Args:
            log_file: Path to CSV file for logging (None = no file logging)
        """
        self.log_file = log_file
        self.state_changes = []  # List of all state changes
        self.metrics_history = []  # List of (timestamp, empty_count, occupied_count)
        
        # Initialize CSV file if provided
        if self.log_file:
            self._init_csv()
    
    def _init_csv(self):
        """Initialize CSV file with headers"""
        if self.log_file and not os.path.exists(self.log_file):
            with open(self.log_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'timestamp', 'space_id', 'old_state', 'new_state',
                    'vehicle_class', 'confidence', 'occupancy_duration'
                ])
    
    def log_state_change(self, space_id: int, old_state: str, new_state: str,
                        timestamp: datetime, vehicle_class: Optional[str] = None,
                        confidence: Optional[float] = None,
                        occupancy_duration: Optional[float] = None):
        """
        Log a state change for a parking space.
        
        Args:
            space_id: ID of the parking space
            old_state: Previous state ('empty' or 'occupied')
            new_state: New state ('empty' or 'occupied')
            timestamp: Timestamp of the change
            vehicle_class: Class of vehicle (if applicable)
            confidence: Detection confidence (if applicable)
            occupancy_duration: Duration space was occupied (if transitioning to empty)
        """
        change_record = {
            'timestamp': timestamp,
            'space_id': space_id,
            'old_state': old_state,
            'new_state': new_state,
            'vehicle_class': vehicle_class or '',
            'confidence': confidence or 0.0,
            'occupancy_duration': occupancy_duration or 0.0
        }
        
        self.state_changes.append(change_record)
        
        # Write to CSV if file logging is enabled
        if self.log_file:
            with open(self.log_file, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    timestamp.isoformat(),
                    space_id,
                    old_state,
                    new_state,
                    vehicle_class or '',
                    confidence or 0.0,
                    occupancy_duration or 0.0
                ])
        
        # Print to console
        time_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{time_str}] Space #{space_id}: {old_state} -> {new_state}")
    
    def log_metrics(self, timestamp: datetime, empty_count: int, occupied_count: int):
        """
        Log current occupancy metrics.
        
        Args:
            timestamp: Current timestamp
            empty_count: Number of empty spaces
            occupied_count: Number of occupied spaces
        """
        self.metrics_history.append({
            'timestamp': timestamp,
            'empty': empty_count,
            'occupied': occupied_count,
            'total': empty_count + occupied_count,
            'occupancy_rate': occupied_count / (empty_count + occupied_count) if (empty_count + occupied_count) > 0 else 0.0
        })
    
    def compute_turnover_rate(self, space_id: Optional[int] = None,
                            time_window_minutes: int = 60) -> float:
        """
        Compute turnover rate (number of state changes per hour).
        
        Args:
            space_id: Specific space ID (None for overall)
            time_window_minutes: Time window in minutes
            
        Returns:
            Turnover rate (changes per hour)
        """
        if not self.state_changes:
            return 0.0
        
        # Filter by space if specified
        changes = [c for c in self.state_changes 
                  if space_id is None or c['space_id'] == space_id]
        
        if not changes:
            return 0.0
        
        # Get time range
        latest_time = max(c['timestamp'] for c in changes)
        cutoff_time = latest_time - pd.Timedelta(minutes=time_window_minutes)
        
        # Count changes in time window
        recent_changes = [c for c in changes if c['timestamp'] >= cutoff_time]
        
        # Convert to changes per hour
        hours = time_window_minutes / 60.0
        return len(recent_changes) / hours if hours > 0 else 0.0
    
    def compute_avg_occupancy_duration(self, space_id: Optional[int] = None) -> float:
        """
        Compute average occupancy duration.
        
        Args:
            space_id: Specific space ID (None for overall)
            
        Returns:
            Average duration in seconds
        """
        durations = []
        for change in self.state_changes:
            if space_id is None or change['space_id'] == space_id:
                if change['occupancy_duration'] > 0:
                    durations.append(change['occupancy_duration'])
        
        return np.mean(durations) if durations else 0.0
    
    def get_peak_hours(self, hour_window: int = 1) -> List[Dict[str, Any]]:
        """
        Identify peak occupancy hours.
        
        Args:
            hour_window: Size of time window in hours
            
        Returns:
            List of peak periods with timestamps and occupancy rates
        """
        if not self.metrics_history:
            return []
        
        # Group by hour
        hourly_data = {}
        for metric in self.metrics_history:
            hour_key = metric['timestamp'].replace(minute=0, second=0, microsecond=0)
            if hour_key not in hourly_data:
                hourly_data[hour_key] = []
            hourly_data[hour_key].append(metric['occupancy_rate'])
        
        # Compute average occupancy per hour
        hourly_avg = {hour: np.mean(rates) for hour, rates in hourly_data.items()}
        
        # Sort by occupancy rate
        sorted_hours = sorted(hourly_avg.items(), key=lambda x: x[1], reverse=True)
        
        # Return top peak hours
        peak_hours = []
        for hour, avg_rate in sorted_hours[:10]:  # Top 10
            peak_hours.append({
                'timestamp': hour.isoformat(),
                'average_occupancy_rate': float(avg_rate)
            })
        
        return peak_hours
    
    def export_metrics_json(self, output_path: str):
        """
        Export metrics to JSON file.
        
        Args:
            output_path: Path to save JSON file
        """
        export_data = {
            'summary': {
                'total_state_changes': len(self.state_changes),
                'total_metrics_recorded': len(self.metrics_history),
                'avg_turnover_rate': self.compute_turnover_rate(),
                'avg_occupancy_duration': self.compute_avg_occupancy_duration(),
                'peak_hours': self.get_peak_hours()
            },
            'state_changes': [
                {
                    'timestamp': c['timestamp'].isoformat(),
                    'space_id': c['space_id'],
                    'old_state': c['old_state'],
                    'new_state': c['new_state'],
                    'vehicle_class': c['vehicle_class'],
                    'confidence': c['confidence'],
                    'occupancy_duration': c['occupancy_duration']
                }
                for c in self.state_changes
            ],
            'metrics_history': [
                {
                    'timestamp': m['timestamp'].isoformat(),
                    'empty': m['empty'],
                    'occupied': m['occupied'],
                    'total': m['total'],
                    'occupancy_rate': m['occupancy_rate']
                }
                for m in self.metrics_history
            ]
        }
        
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', 
                   exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        print(f"Metrics exported to: {output_path}")
    
    def export_metrics_csv(self, output_path: str):
        """
        Export metrics history to CSV file.
        
        Args:
            output_path: Path to save CSV file
        """
        if not self.metrics_history:
            print("No metrics to export")
            return
        
        df = pd.DataFrame(self.metrics_history)
        df['timestamp'] = df['timestamp'].apply(lambda x: x.isoformat())
        
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', 
                   exist_ok=True)
        
        df.to_csv(output_path, index=False)
        print(f"Metrics CSV exported to: {output_path}")

