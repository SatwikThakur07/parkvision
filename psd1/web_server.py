"""
Web Server Module
Optional HTTP server for remote monitoring of parking lot status.
"""

from flask import Flask, jsonify, render_template_string
import threading
from datetime import datetime
from typing import Optional, Callable
from parking_space import ParkingSpaceManager
from logger import ParkingLogger


app = Flask(__name__)

# Global state (set by main application)
space_manager: Optional[ParkingSpaceManager] = None
logger: Optional[ParkingLogger] = None
last_update_time: Optional[datetime] = None

# Update function to be called periodically
update_callback: Optional[Callable] = None


def init_web_server(manager: ParkingSpaceManager, parking_logger: ParkingLogger,
                   update_fn: Optional[Callable] = None):
    """
    Initialize the web server with parking space manager and logger.
    
    Args:
        manager: ParkingSpaceManager instance
        parking_logger: ParkingLogger instance
        update_fn: Optional callback function to trigger updates
    """
    global space_manager, logger, update_callback
    space_manager = manager
    logger = parking_logger
    update_callback = update_fn


@app.route('/')
def index():
    """Main dashboard page"""
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Parking Lot Monitor</title>
        <meta http-equiv="refresh" content="5">
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 20px;
                background: #f5f5f5;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
                background: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            h1 {
                color: #333;
            }
            .stats {
                display: flex;
                gap: 20px;
                margin: 20px 0;
            }
            .stat-card {
                flex: 1;
                padding: 20px;
                border-radius: 8px;
                text-align: center;
            }
            .stat-card.empty {
                background: #d4edda;
                color: #155724;
            }
            .stat-card.occupied {
                background: #f8d7da;
                color: #721c24;
            }
            .stat-value {
                font-size: 48px;
                font-weight: bold;
                margin: 10px 0;
            }
            .stat-label {
                font-size: 18px;
            }
            .last-update {
                color: #666;
                font-size: 14px;
                margin-top: 20px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Parking Lot Monitor</h1>
            <div class="stats">
                <div class="stat-card empty">
                    <div class="stat-label">Empty Spaces</div>
                    <div class="stat-value" id="empty-count">-</div>
                </div>
                <div class="stat-card occupied">
                    <div class="stat-label">Occupied Spaces</div>
                    <div class="stat-value" id="occupied-count">-</div>
                </div>
            </div>
            <div class="last-update" id="last-update">Loading...</div>
        </div>
        <script>
            fetch('/api/status')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('empty-count').textContent = data.empty;
                    document.getElementById('occupied-count').textContent = data.occupied;
                    document.getElementById('last-update').textContent = 
                        'Last updated: ' + new Date(data.timestamp).toLocaleString();
                });
        </script>
    </body>
    </html>
    """
    return render_template_string(html_template)


@app.route('/api/status')
def api_status():
    """API endpoint for current parking lot status"""
    global space_manager, last_update_time, update_callback
    
    if space_manager is None:
        return jsonify({'error': 'Parking space manager not initialized'}), 500
    
    # Trigger update if callback is set
    if update_callback:
        try:
            update_callback()
        except:
            pass
    
    empty, occupied = space_manager.get_counts()
    occupancy_rate = space_manager.get_occupancy_rate()
    last_update_time = datetime.now()
    
    return jsonify({
        'empty': empty,
        'occupied': occupied,
        'total': space_manager.total_spaces,
        'occupancy_rate': occupancy_rate,
        'timestamp': last_update_time.isoformat()
    })


@app.route('/api/spaces')
def api_spaces():
    """API endpoint for detailed space information"""
    global space_manager
    
    if space_manager is None:
        return jsonify({'error': 'Parking space manager not initialized'}), 500
    
    spaces_data = []
    for space in space_manager.spaces:
        spaces_data.append({
            'id': space.space_id,
            'state': space.state.value,
            'vehicle_count': space.vehicle_count,
            'centroid': space.get_centroid(),
            'last_change_time': space.last_change_time.isoformat() if space.last_change_time else None
        })
    
    return jsonify({
        'spaces': spaces_data,
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/metrics')
def api_metrics():
    """API endpoint for parking metrics"""
    global logger
    
    if logger is None:
        return jsonify({'error': 'Logger not initialized'}), 500
    
    return jsonify({
        'turnover_rate': logger.compute_turnover_rate(),
        'avg_occupancy_duration': logger.compute_avg_occupancy_duration(),
        'peak_hours': logger.get_peak_hours(),
        'total_changes': len(logger.state_changes),
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/changes')
def api_changes():
    """API endpoint for recent state changes"""
    global logger
    
    if logger is None:
        return jsonify({'error': 'Logger not initialized'}), 500
    
    # Get last 50 changes
    recent_changes = logger.state_changes[-50:]
    
    changes_data = [{
        'timestamp': c['timestamp'].isoformat(),
        'space_id': c['space_id'],
        'old_state': c['old_state'],
        'new_state': c['new_state'],
        'vehicle_class': c['vehicle_class']
    } for c in recent_changes]
    
    return jsonify({
        'changes': changes_data,
        'count': len(changes_data)
    })


def run_web_server(host: str = '0.0.0.0', port: int = 5000, debug: bool = False):
    """
    Run the Flask web server.
    
    Args:
        host: Host to bind to
        port: Port to bind to
        debug: Enable debug mode
    """
    print(f"Starting web server on http://{host}:{port}")
    app.run(host=host, port=port, debug=debug, threaded=True)


def start_web_server_thread(host: str = '0.0.0.0', port: int = 5000):
    """
    Start web server in a separate thread.
    
    Args:
        host: Host to bind to
        port: Port to bind to
    """
    server_thread = threading.Thread(
        target=run_web_server,
        args=(host, port, False),
        daemon=True
    )
    server_thread.start()
    return server_thread

