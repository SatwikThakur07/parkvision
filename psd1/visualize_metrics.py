#!/usr/bin/env python3
"""
Metrics Visualization Tool
Generate graphs and charts from parking lot metrics data.
"""

import argparse
import json
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import os


def load_metrics_json(json_path: str):
    """Load metrics from JSON file"""
    with open(json_path, 'r') as f:
        data = json.load(f)
    return data


def plot_occupancy_over_time(metrics_data: dict, output_path: str = None):
    """Plot occupancy over time"""
    if 'metrics_history' not in metrics_data or not metrics_data['metrics_history']:
        print("No metrics history to plot")
        return
    
    df = pd.DataFrame(metrics_data['metrics_history'])
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    ax.plot(df['timestamp'], df['occupied'], label='Occupied', color='red', linewidth=2)
    ax.plot(df['timestamp'], df['empty'], label='Empty', color='green', linewidth=2)
    ax.fill_between(df['timestamp'], 0, df['occupied'], alpha=0.3, color='red')
    ax.fill_between(df['timestamp'], 0, df['empty'], alpha=0.3, color='green')
    
    ax.set_xlabel('Time', fontsize=12)
    ax.set_ylabel('Number of Spaces', fontsize=12)
    ax.set_title('Parking Lot Occupancy Over Time', fontsize=14, fontweight='bold')
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3)
    
    # Format x-axis dates
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
    plt.xticks(rotation=45)
    
    plt.tight_layout()
    
    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"Saved occupancy plot to: {output_path}")
    else:
        plt.show()


def plot_occupancy_rate(metrics_data: dict, output_path: str = None):
    """Plot occupancy rate over time"""
    if 'metrics_history' not in metrics_data or not metrics_data['metrics_history']:
        print("No metrics history to plot")
        return
    
    df = pd.DataFrame(metrics_data['metrics_history'])
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    ax.plot(df['timestamp'], df['occupancy_rate'] * 100, 
           color='blue', linewidth=2, label='Occupancy Rate')
    ax.fill_between(df['timestamp'], 0, df['occupancy_rate'] * 100, 
                    alpha=0.3, color='blue')
    
    ax.axhline(y=50, color='orange', linestyle='--', linewidth=1, label='50% Threshold')
    
    ax.set_xlabel('Time', fontsize=12)
    ax.set_ylabel('Occupancy Rate (%)', fontsize=12)
    ax.set_title('Parking Lot Occupancy Rate Over Time', fontsize=14, fontweight='bold')
    ax.set_ylim(0, 100)
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3)
    
    # Format x-axis dates
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
    plt.xticks(rotation=45)
    
    plt.tight_layout()
    
    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"Saved occupancy rate plot to: {output_path}")
    else:
        plt.show()


def plot_state_changes(metrics_data: dict, output_path: str = None):
    """Plot state changes timeline"""
    if 'state_changes' not in metrics_data or not metrics_data['state_changes']:
        print("No state changes to plot")
        return
    
    df = pd.DataFrame(metrics_data['state_changes'])
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Count changes per hour
    df['hour'] = df['timestamp'].dt.floor('H')
    hourly_changes = df.groupby('hour').size()
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    ax.bar(hourly_changes.index, hourly_changes.values, 
          color='purple', alpha=0.7, width=0.03)
    
    ax.set_xlabel('Time', fontsize=12)
    ax.set_ylabel('Number of State Changes', fontsize=12)
    ax.set_title('Parking Space State Changes Over Time', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3, axis='y')
    
    # Format x-axis dates
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    plt.xticks(rotation=45)
    
    plt.tight_layout()
    
    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"Saved state changes plot to: {output_path}")
    else:
        plt.show()


def print_summary(metrics_data: dict):
    """Print summary statistics"""
    summary = metrics_data.get('summary', {})
    
    print("\n" + "="*50)
    print("PARKING LOT METRICS SUMMARY")
    print("="*50)
    print(f"Total State Changes: {summary.get('total_state_changes', 0)}")
    print(f"Total Metrics Recorded: {summary.get('total_metrics_recorded', 0)}")
    print(f"Average Turnover Rate: {summary.get('avg_turnover_rate', 0):.2f} changes/hour")
    print(f"Average Occupancy Duration: {summary.get('avg_occupancy_duration', 0):.2f} seconds")
    
    peak_hours = summary.get('peak_hours', [])
    if peak_hours:
        print("\nTop Peak Hours:")
        for i, peak in enumerate(peak_hours[:5], 1):
            timestamp = peak['timestamp']
            rate = peak['average_occupancy_rate'] * 100
            print(f"  {i}. {timestamp}: {rate:.1f}% occupancy")
    
    print("="*50 + "\n")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Visualize parking lot metrics from JSON export"
    )
    parser.add_argument('input', type=str,
                       help='Path to metrics JSON file')
    parser.add_argument('--output-dir', type=str, default='plots',
                       help='Output directory for plots (default: plots)')
    parser.add_argument('--no-display', action='store_true',
                       help='Save plots without displaying')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input):
        print(f"Error: File not found: {args.input}")
        return
    
    # Load metrics
    print(f"Loading metrics from: {args.input}")
    metrics_data = load_metrics_json(args.input)
    
    # Print summary
    print_summary(metrics_data)
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Generate plots
    base_name = os.path.splitext(os.path.basename(args.input))[0]
    
    plot_occupancy_over_time(
        metrics_data,
        output_path=os.path.join(args.output_dir, f"{base_name}_occupancy.png") if args.no_display else None
    )
    
    plot_occupancy_rate(
        metrics_data,
        output_path=os.path.join(args.output_dir, f"{base_name}_rate.png") if args.no_display else None
    )
    
    plot_state_changes(
        metrics_data,
        output_path=os.path.join(args.output_dir, f"{base_name}_changes.png") if args.no_display else None
    )
    
    if not args.no_display:
        print("\nClose plot windows to exit.")


if __name__ == '__main__':
    main()

