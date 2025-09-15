#!/usr/bin/env python3
"""
Test script to check if the server components are working
"""
import requests
import time
import json
from pathlib import Path

def test_server():
    """Test the server endpoints"""
    base_url = "http://localhost:8000"
    
    print("Testing HERFOO_TRADES Server...")
    print("=" * 50)
    
    # Test basic connectivity
    try:
        response = requests.get(f"{base_url}/api/status", timeout=5)
        if response.status_code == 200:
            print("✓ Server is running and responding")
            data = response.json()
            print(f"  Current position: {data.get('position', 'None')}")
            print(f"  Total P&L: {data.get('total_pnl', 0)}")
        else:
            print(f"✗ Server responded with status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"✗ Cannot connect to server: {e}")
        print("  Make sure the server is running on http://localhost:8000")
        return False
    
    # Test symbol configuration
    try:
        response = requests.get(f"{base_url}/api/symbol", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Symbol configured: {data.get('display', 'Unknown')}")
            print(f"  Breeze code: {data.get('breeze_code', 'Unknown')}")
        else:
            print(f"✗ Symbol API error: {response.status_code}")
    except Exception as e:
        print(f"✗ Symbol test failed: {e}")
    
    # Test LTP (Last Traded Price)
    try:
        response = requests.get(f"{base_url}/api/ltp", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✓ LTP retrieved: {data.get('ltp', 'N/A')} for {data.get('symbol', 'Unknown')}")
        else:
            print(f"✗ LTP API error: {response.status_code}")
    except Exception as e:
        print(f"✗ LTP test failed: {e}")
    
    # Test trader status
    try:
        response = requests.get(f"{base_url}/api/trader/status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Trader status: {data.get('status', 'Unknown')}")
        else:
            print(f"✗ Trader status API error: {response.status_code}")
    except Exception as e:
        print(f"✗ Trader status test failed: {e}")
    
    print("=" * 50)
    print("Test completed!")
    return True

def check_config_files():
    """Check if required config files exist and are valid"""
    print("Checking configuration files...")
    print("=" * 50)
    
    required_files = {
        "creds.config": "API credentials",
        "rules.config": "Trading rules", 
        "stocksymbol.txt": "Stock symbol"
    }
    
    for filename, description in required_files.items():
        file_path = Path(filename)
        if file_path.exists():
            try:
                if filename.endswith('.json') or filename == 'creds.config':
                    with open(file_path, 'r') as f:
                        json.load(f)
                    print(f"✓ {description}: Valid JSON")
                else:
                    content = file_path.read_text().strip()
                    if content:
                        print(f"✓ {description}: {content}")
                    else:
                        print(f"✗ {description}: File is empty")
            except Exception as e:
                print(f"✗ {description}: Invalid format - {e}")
        else:
            print(f"✗ {description}: File missing")
    
    print("=" * 50)

if __name__ == "__main__":
    check_config_files()
    print()
    test_server()
