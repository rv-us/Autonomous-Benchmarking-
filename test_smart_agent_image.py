"""
test_smart_agent_image.py

Test script to verify the new image analysis capabilities in the smart Picar-X agent.
This script tests the new image tools: capture_image_tool, analyze_image_tool, and captureAndAnalyze_tool.
"""

import os
import sys
from picarx_agent_smart import PicarXSmartAgent, capture_image_tool, analyze_image_tool, captureAndAnalyze_tool
from keys import OPENAI_API_KEY

# Set the environment variable for OpenAI Agents SDK
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

def test_image_tools():
    """Test the new image analysis tools."""
    print("Testing Smart Agent Image Capabilities")
    print("=" * 50)
    
    # Check for API key
    if not OPENAI_API_KEY:
        print("Error: OPENAI_API_KEY not found in keys.py")
        print("Please add your OpenAI API key to keys.py")
        return
    
    try:
        # Initialize the smart agent
        print("🤖 Initializing PicarXSmartAgent...")
        agent = PicarXSmartAgent()
        print("✅ Smart agent initialized successfully!")
        
        # Test 1: Direct tool calls
        print("\n1. Testing direct tool calls:")
        print("-" * 30)
        
        # Test capture_image_tool
        print("📸 Testing capture_image_tool...")
        result = capture_image_tool("test_capture.jpg")
        print(f"Capture result: {result}")
        
        # Test analyze_image_tool (if test image exists)
        if os.path.exists("test_capture.jpg"):
            print("\n🔍 Testing analyze_image_tool...")
            result = analyze_image_tool("test_capture.jpg", "Describe what you see in this image")
            print(f"Analysis result: {result}")
        else:
            print("⚠️  No test image found, skipping analysis test")
        
        # Test captureAndAnalyze_tool
        print("\n📸🔍 Testing captureAndAnalyze_tool...")
        result = captureAndAnalyze_tool("test_capture_analyze.jpg", "What do you see in this image?")
        print(f"Capture and analyze result: {result}")
        
        # Test 2: Through the agent
        print("\n2. Testing through PicarXSmartAgent:")
        print("-" * 30)
        
        # Test image capture command
        print("📸 Testing 'Take a photo' command...")
        result = agent.process_request("Take a photo using the camera")
        print(f"Agent result: {result}")
        
        # Test image analysis command
        print("\n🔍 Testing 'Take photo and analyze' command...")
        result = agent.process_request("Take a photo and analyze what you see in the image")
        print(f"Agent result: {result}")
        
        # Test 3: Complex vision task
        print("\n3. Testing complex vision task:")
        print("-" * 30)
        
        print("🎯 Testing 'Find objects in the room' command...")
        result = agent.process_request("Take a photo and identify any objects you can see in the room")
        print(f"Complex vision result: {result}")
        
        print("\n" + "=" * 50)
        print("✅ Image analysis testing completed!")
        print("The smart agent now has full vision capabilities!")
        
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()

def main():
    """Main function to run the image capabilities test."""
    test_image_tools()

if __name__ == "__main__":
    main()
