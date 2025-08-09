#!/usr/bin/env python3
"""
test_camera.py

Simple script to test camera functionality before running the full agent.
"""

import time
import sys
from picarx_primitives import init_camera, capture_image, close_camera

def test_camera():
    """Test camera initialization and image capture."""
    print("Testing Picar-X Camera System...")
    
    try:
        # Initialize camera
        print("1. Initializing camera...")
        init_camera()
        print("   ✓ Camera initialized successfully")
        
        # Wait a moment for stabilization
        print("2. Waiting for camera to stabilize...")
        time.sleep(2)
        print("   ✓ Camera ready")
        
        # Take a test photo
        print("3. Capturing test image...")
        capture_image("test_photo.jpg")
        print("   ✓ Test image captured as test_photo.jpg")
        
        # Test multiple captures
        print("4. Testing multiple captures...")
        for i in range(3):
            capture_image(f"test_photo_{i+1}.jpg")
            print(f"   ✓ Image {i+1} captured")
            time.sleep(1)
        
        print("\n" + "="*50)
        print("Camera test completed successfully!")
        print("You can now run the full agent with:")
        print("  python picarx_agent_with_camera.py")
        print("="*50)
        
    except Exception as e:
        print(f"\n❌ Camera test failed: {str(e)}")
        print("\nTroubleshooting:")
        print("1. Make sure the camera is connected")
        print("2. Check if vilib is installed: pip install vilib")
        print("3. Ensure you're running on the Raspberry Pi")
        print("4. Try running with sudo if needed")
        return False
        
    finally:
        try:
            close_camera()
            print("Camera closed cleanly")
        except:
            pass
    
    return True

if __name__ == "__main__":
    success = test_camera()
    sys.exit(0 if success else 1)