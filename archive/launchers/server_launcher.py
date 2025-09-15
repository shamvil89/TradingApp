#!/usr/bin/env python3
"""
HERFOO_TRADES Server Launcher
Standalone executable launcher for the FastAPI server
"""
import subprocess
import sys
import os
import webbrowser
import time
import threading
from pathlib import Path

def open_browser_delayed():
    """Open browser after a short delay"""
    time.sleep(3)  # Wait 3 seconds for server to start
    try:
        webbrowser.open("http://localhost:8000")
    except:
        pass

def main():
    print("HERFOO_TRADES Server Launcher")
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
        subprocess.run(cmd)
        
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"Error starting server: {e}")
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()
