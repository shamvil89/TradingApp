#!/usr/bin/env python3
"""
Build executable for HERFOO_TRADES Server
This script will create a standalone executable using PyInstaller
"""
import subprocess
import sys
import os
from pathlib import Path

def install_pyinstaller():
    """Install PyInstaller if not already installed"""
    try:
        import PyInstaller
        print("PyInstaller is already installed")
    except ImportError:
        print("Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

def build_executable():
    """Build the executable"""
    script_dir = Path(__file__).parent.absolute()
    
    # PyInstaller command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",  # Create a single executable file
        "--windowed",  # Don't show console window (remove this if you want to see console)
        "--name=HERFOO_TRADES_Server",
        "--add-data=web;web",  # Include web directory
        "--add-data=creds.config;.",  # Include config files
        "--add-data=rules.config;.",
        "--add-data=stocksymbol.txt;.",
        "--hidden-import=uvicorn",
        "--hidden-import=fastapi",
        "--hidden-import=breeze_connect",
        "--hidden-import=yfinance",
        "--hidden-import=pandas",
        "start_server.py"
    ]
    
    print("Building executable...")
    print(f"Command: {' '.join(cmd)}")
    
    try:
        subprocess.run(cmd, cwd=script_dir, check=True)
        print("\n" + "="*50)
        print("SUCCESS! Executable created in 'dist' folder")
        print("You can now run: dist\\HERFOO_TRADES_Server.exe")
        print("="*50)
    except subprocess.CalledProcessError as e:
        print(f"Error building executable: {e}")
        return False
    
    return True

def main():
    print("HERFOO_TRADES Server Executable Builder")
    print("=" * 50)
    
    # Install PyInstaller
    install_pyinstaller()
    
    # Build executable
    if build_executable():
        print("\nBuild completed successfully!")
    else:
        print("\nBuild failed!")
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()
