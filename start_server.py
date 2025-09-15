#!/usr/bin/env python3
"""
HERFOO_TRADES Server Starter
Simple script to start the FastAPI server
"""
import subprocess
import sys
import os
from pathlib import Path
from typing import Optional

def _frozen_base_dir() -> Optional[Path]:
    try:
        # When packaged with PyInstaller --onefile, data are unpacked to sys._MEIPASS
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            return Path(meipass)
    except Exception:
        pass
    return None

def main():
    print("Starting HERFOO_TRADES Server...")
    print("=" * 50)
    
    # Set working directory so relative paths (e.g., web/, config files) resolve
    base_dir = _frozen_base_dir() or Path(__file__).parent.absolute()
    os.chdir(base_dir)
    
    try:
        # If running as a frozen executable, launch uvicorn in-process to avoid
        # recursive self-invocation via `sys.executable -m uvicorn`.
        if getattr(sys, 'frozen', False):
            print("Detected frozen executable; starting Uvicorn in-process")
            print(f"Server will be available at: http://localhost:8000")
            print(f"Web dashboard: http://localhost:8000/web")
            print("Press Ctrl+C to stop the server")
            print("=" * 50)
            # Force inclusion of server module in PyInstaller build, and run via object
            import uvicorn  # type: ignore
            try:
                import server  # type: ignore
                uvicorn.run(server.app, host="0.0.0.0", port=8000, reload=False, log_level="info")
            except Exception as e:
                print(f"Failed to import or start server: {e}")
                raise
        else:
            # Start the server via the current Python interpreter
            cmd = [sys.executable, "-m", "uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
            print(f"Running: {' '.join(cmd)}")
            print(f"Server will be available at: http://localhost:8000")
            print(f"Web dashboard: http://localhost:8000/web")
            print("Press Ctrl+C to stop the server")
            print("=" * 50)
            subprocess.run(cmd)
        
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"Error starting server: {e}")
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()
