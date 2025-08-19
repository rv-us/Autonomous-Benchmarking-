"""
test_image_upload_sync.py

Synchronous test script to verify image upload functionality with OpenAI Agents SDK.
This is a simpler version for easier testing before we integrate it into the smart agent.
"""

import base64
import os
import sys
from agents import Agent, Runner
from keys import OPENAI_API_KEY

def test_image_upload(image_path: str):
    """Test uploading an image to the chat."""
    print(f"Testing image upload with: {image_path}")
    print("=" * 50)
    
    # Check if image file exists
    if not os.path.exists(image_path):
        print(f"❌ Error: Image file '{image_path}' not found!")
        return False
    
    try:
        # Read and encode the image
        print(f"📸 Reading image file: {image_path}")
        with open(image_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode("utf-8")
        print(f"✅ Image encoded successfully (size: {len(base64_image)} chars)")
        
        # Create the agent
        print("🤖 Creating test agent...")
        agent = Agent(
            name="Image Test Assistant",
            model="gpt-4o",  # Using gpt-4o for better image understanding
            instructions="""You are a test assistant that can analyze images. 
            When given an image, describe what you see and provide any relevant observations.
            Be detailed but concise in your analysis.""",
        )
        
        # Create message with image
        print("📤 Creating message with image...")
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Please analyze this image and tell me what you see."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ]
        
        # Send the message
        print("🚀 Sending message to agent...")
        result = Runner.run_sync(agent, messages)
        
        print("✅ Image upload test successful!")
        print(f"📝 Agent response: {result.final_output}")
        return True
        
    except Exception as e:
        print(f"❌ Error during image upload test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_multiple_images():
    """Test with multiple image formats and scenarios."""
    print("\n🧪 Testing multiple image scenarios...")
    print("=" * 50)
    
    # Test scenarios
    test_cases = [
        "env_capture.jpg",
        "environment_capture.jpg", 
    ]
    
    for image_path in test_cases:
        if os.path.exists(image_path):
            print(f"\n📸 Testing with: {image_path}")
            success = test_image_upload(image_path)
            if success:
                print(f"✅ {image_path} - Test passed")
            else:
                print(f"❌ {image_path} - Test failed")
        else:
            print(f"⚠️  {image_path} - File not found, skipping")

def main():
    """Main function to run the image upload test."""
    # Check for API key
    if not OPENAI_API_KEY:
        print("Error: OPENAI_API_KEY not found in keys.py")
        print("Please add your OpenAI API key to keys.py")
        sys.exit(1)
    
    # Check command line arguments
    if len(sys.argv) > 1:
        # Test specific image
        image_path = sys.argv[1]
        print(f"Testing specific image: {image_path}")
        test_image_upload(image_path)
    else:
        # Test multiple images
        print("No specific image provided, testing multiple scenarios...")
        test_multiple_images()

if __name__ == "__main__":
    main()
