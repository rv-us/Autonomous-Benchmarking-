"""
test_servo_tracking.py

Simple test script to verify servo angle tracking functionality.
This script tests the get_robot_state_tool and demonstrates how servo angles are tracked.
"""

import os
import sys
from picarx_agent_smart import PicarXSmartAgent, get_robot_state_tool
from keys import OPENAI_API_KEY

def test_servo_tracking():
    """Test the servo angle tracking functionality."""
    print("Testing Servo Angle Tracking")
    print("=" * 40)
    
    # Test 1: Direct tool call
    print("\n1. Testing get_robot_state_tool directly:")
    try:
        state = get_robot_state_tool()
        print(f"Robot State: {state}")
        print("✅ Direct tool call successful")
    except Exception as e:
        print(f"❌ Direct tool call failed: {e}")
    
    # Test 2: Through the agent
    print("\n2. Testing through PicarXSmartAgent:")
    try:
        agent = PicarXSmartAgent()
        state = agent.get_current_robot_state()
        print(f"Robot State: {state}")
        print("✅ Agent method call successful")
    except Exception as e:
        print(f"❌ Agent method call failed: {e}")
    
    # Test 3: Test orchestrator with robot state
    print("\n3. Testing orchestrator decision with robot state:")
    try:
        agent = PicarXSmartAgent()
        result = agent.process_request("Turn left 30 degrees")
        print(f"Orchestrator Result: {result}")
        print("✅ Orchestrator decision with robot state successful")
    except Exception as e:
        print(f"❌ Orchestrator test failed: {e}")
    
    print("\n" + "=" * 40)
    print("Servo tracking test completed!")

if __name__ == "__main__":
    # Check for API key
    if not OPENAI_API_KEY:
        print("Error: OPENAI_API_KEY not found in keys.py")
        print("Please add your OpenAI API key to keys.py")
        sys.exit(1)
    
    test_servo_tracking()
