#!/usr/bin/env python3
"""
Test script to verify real-time API endpoints are working
"""
import requests
import json
from pathlib import Path

BASE_URL = "http://localhost:8000"

def test_plate_detection():
    """Test plate detection endpoint"""
    print("\n=== Testing Plate Detection ===")
    
    # Create a dummy image (1x1 pixel)
    import numpy as np
    from PIL import Image
    import io
    
    # Create a simple test image
    img = Image.new('RGB', (640, 480), color='black')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes.seek(0)
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/realtime/plate-detect",
            files={'file': ('test.jpg', img_bytes, 'image/jpeg')},
            timeout=10
        )
        print(f"Status: {response.status_code}")
        if response.ok:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            return True
        else:
            print(f"Error: {response.text}")
            return False
    except Exception as e:
        print(f"Exception: {e}")
        return False

def test_get_plates():
    """Test get plates endpoint"""
    print("\n=== Testing Get Plates ===")
    try:
        response = requests.get(f"{BASE_URL}/api/realtime/plates?limit=10", timeout=5)
        print(f"Status: {response.status_code}")
        if response.ok:
            data = response.json()
            print(f"Plates: {len(data.get('plates', []))} found")
            print(f"Today entries: {data.get('today_entries', 0)}")
            return True
        else:
            print(f"Error: {response.text}")
            return False
    except Exception as e:
        print(f"Exception: {e}")
        return False

def test_dashboard():
    """Test dashboard endpoint"""
    print("\n=== Testing Dashboard ===")
    try:
        response = requests.get(f"{BASE_URL}/api/realtime/dashboard", timeout=5)
        print(f"Status: {response.status_code}")
        if response.ok:
            data = response.json()
            print(f"Parking: {data.get('parking', {})}")
            print(f"Plates: {len(data.get('plates', {}).get('recent', []))} recent")
            return True
        else:
            print(f"Error: {response.text}")
            return False
    except Exception as e:
        print(f"Exception: {e}")
        return False

if __name__ == "__main__":
    print("Testing Real-time API Endpoints")
    print("=" * 50)
    
    test_plate_detection()
    test_get_plates()
    test_dashboard()
    
    print("\n" + "=" * 50)
    print("Test complete. Check the output above for any errors.")

