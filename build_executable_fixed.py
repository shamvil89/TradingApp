#!/usr/bin/env python3
"""
Build executable for HERFOO_TRADES Server (Fixed Version)
This script will create a standalone executable using PyInstaller
WITHOUT the --windowed flag so errors are visible
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
    
    # PyInstaller command - REMOVED --windowed flag so console is visible
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",  # Create a single executable file
        # "--windowed",  # REMOVED - This hides console and causes issues
        "--name=HERFOO_TRADES_Server_Fixed",
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
        print("You can now run: dist\\HERFOO_TRADES_Server_Fixed.exe")
        print("This version shows console output so you can see any errors")
        print("="*50)
    except subprocess.CalledProcessError as e:
        print(f"Error building executable: {e}")
        return False
    
    return True

def main():
    print("HERFOO_TRADES Server Executable Builder (Fixed Version)")
    print("=" * 50)
    
    # Install PyInstaller
    install_pyinstaller()
    
    # Build executable
    if build_executable():
        print("\nBuild completed successfully!")
        print("The new executable will show console output for debugging")
    else:
        print("\nBuild failed!")
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()
