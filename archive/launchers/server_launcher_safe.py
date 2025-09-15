#!/usr/bin/env python3
"""
HERFOO_TRADES Server Launcher (Safe Version)
Standalone executable launcher for the FastAPI server with better error handling
"""
import subprocess
import sys
import os
import webbrowser
import time
import threading
import signal
from pathlib import Path

# Global variable to track if server is running
_server_process = None

def signal_handler(signum, frame):
    """Handle Ctrl+C gracefully"""
    print("\nShutting down server...")
    if _server_process:
        try:
            _server_process.terminate()
            _server_process.wait(timeout=5)
        except:
            try:
                _server_process.kill()
            except:
                pass
    sys.exit(0)

def open_browser_delayed():
    """Open browser after a short delay"""
    time.sleep(5)  # Wait 5 seconds for server to start
    try:
        webbrowser.open("http://localhost:8000")
        print("Browser opened to http://localhost:8000")
    except Exception as e:
        print(f"Could not open browser: {e}")
        print("Please manually open: http://localhost:8000")

def check_port_available(port):
    """Check if port is available"""
    import socket
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('localhost', port))
            return True
    except OSError:
        return False

def main():
    global _server_process
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("HERFOO_TRADES Server Launcher (Safe Version)")
    print("=" * 50)
    
    # Get the directory where this script is located
    script_dir = Path(__file__).parent.absolute()
    os.chdir(script_dir)
    
    # Check if required files exist
    required_files = ["server.py", "creds.config", "rules.config", "stocksymbol.txt"]
    missing_files = []
    
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)
    
    if missing_files:
        print("ERROR: Missing required files:")
        for file in missing_files:
            print(f"  - {file}")
        print("\nPlease ensure all configuration files are present.")
        input("Press Enter to exit...")
        return
    
    # Check if port 8000 is available
    if not check_port_available(8000):
        print("ERROR: Port 8000 is already in use!")
        print("Please close any other applications using port 8000")
        input("Press Enter to exit...")
        return
    
    print("Starting HERFOO_TRADES Server...")
    print("Server will be available at: http://localhost:8000")
    print("Web dashboard: http://localhost:8000/web")
    print("Press Ctrl+C to stop the server")
    print("=" * 50)
    
    try:
        # Start browser opening in background
        browser_thread = threading.Thread(target=open_browser_delayed, daemon=True)
        browser_thread.start()
        
        # Start the server
        cmd = [sys.executable, "-m", "uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
        print(f"Running command: {' '.join(cmd)}")
        
        _server_process = subprocess.Popen(cmd)
        
        # Wait for the process to complete
        _server_process.wait()
        
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"Error starting server: {e}")
        print("Please check your configuration files and try again")
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()
