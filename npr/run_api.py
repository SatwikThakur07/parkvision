"""Run the API server"""
import uvicorn
from src.config import settings

if __name__ == "__main__":
    # Use port 8001 if 8000 is occupied
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    port = settings.api_port
    if sock.connect_ex(('localhost', port)) == 0:
        print(f"⚠️  Port {port} is already in use. Using port 8001 instead.")
        port = 8001
    sock.close()
    
    uvicorn.run(
        "src.api:app",
        host=settings.api_host,
        port=port,
        log_level=settings.log_level.lower(),
        reload=settings.debug
    )

