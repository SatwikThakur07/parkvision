#!/usr/bin/env python3
"""
Run the integrated API server
"""

import uvicorn
import sys
import socket
from pathlib import Path

# Add project directories to path
base_dir = Path(__file__).parent
sys.path.insert(0, str(base_dir / "npr" / "src"))
sys.path.insert(0, str(base_dir / "psd1"))

def find_available_port(start_port=8000, max_attempts=10):
    """Find an available port starting from start_port"""
    for port in range(start_port, start_port + max_attempts):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.bind(('localhost', port))
            sock.close()
            return port
        except OSError:
            continue
    raise RuntimeError(f"Could not find an available port in range {start_port}-{start_port + max_attempts}")

if __name__ == "__main__":
    # Find available port
    port = find_available_port(8000)
    
    print("=" * 60)
    print("Starting Integrated Vehicle Monitoring System")
    print("=" * 60)
    if port != 8000:
        print(f"⚠️  Port 8000 is already in use. Using port {port} instead.")
    print(f"Access the frontend at: http://localhost:{port}")
    print(f"API documentation at: http://localhost:{port}/docs")
    print("=" * 60)
    
    uvicorn.run(
        "integrated_api:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )

