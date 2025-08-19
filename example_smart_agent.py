"""
example_smart_agent.py

Example usage of the smart Picar-X agent with orchestrator-judge pattern.
This script demonstrates how the agent automatically decides between immediate action
and planning, with memory persistence.
"""

import os
from picarx_agent_smart import PicarXSmartAgent
from keys import OPENAI_API_KEY

# Set the environment variable for OpenAI Agents SDK
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

def main():
    """Example usage of the smart Picar-X agent."""
    # Check for API key
    if not OPENAI_API_KEY:
        print("Error: OPENAI_API_KEY not found in keys.py")
        print("Please add your OpenAI API key to keys.py")
        return
    
    # Initialize the smart agent
    agent = PicarXSmartAgent()
    
    print("Smart Picar-X Agent Example")
    print("=" * 50)
    
    # Example 1: Simple command (should trigger immediate action)
    print("\nExample 1: Simple command - 'Drive forward at speed 30'")
    print("This should trigger IMMEDIATE action...")
    result = agent.process_request("Drive forward at speed 30")
    print(f"Result: {result}")
    
    # Example 2: Complex command (should trigger planning)
    print("\nExample 2: Complex command - 'Explore the room and find the exit'")
    print("This should trigger NEEDS PLAN...")
    result = agent.process_request("Explore the room and find the exit")
    print(f"Result: {result}")
    
    # Example 3: Check plan progress
    print("\nExample 3: Check plan progress")
    result = agent.check_plan_progress()
    print(f"Progress: {result}")
    
    # Example 4: Execute a specific step
    print("\nExample 4: Execute a specific step")
    result = agent.execute_plan_step("Take a picture of the current view")
    print(f"Step execution: {result}")
    
    # Example 5: Check robot state
    print("\nExample 5: Check current robot state")
    result = agent.get_current_robot_state()
    print(f"Robot State: {result}")
    
    # Example 6: Image capture and analysis
    print("\nExample 6: Image capture and analysis - 'Take a photo and analyze what you see'")
    result = agent.process_request("Take a photo and analyze what you see")
    print(f"Result: {result}")
    
    # Example 7: Another simple command
    print("\nExample 7: Another simple command - 'Turn left 45 degrees'")
    result = agent.process_request("Turn left 45 degrees")
    print(f"Result: {result}")
    
    print("\nSmart agent example completed.")
    print("The agent automatically decided when to act immediately vs. when to plan!")
    print("All agents now have access to current robot state and image analysis for better decision making!")

if __name__ == "__main__":
    main()
