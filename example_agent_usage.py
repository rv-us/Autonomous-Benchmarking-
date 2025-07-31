"""
example_agent_usage.py

Example usage of the Picar-X agent using OpenAI Agents SDK.
This script demonstrates how to use the agent programmatically.
"""

import os
from picarx_agent import PicarXAgent
from agents import Runner
from keys import OPENAI_API_KEY

def main():
    """Example usage of the Picar-X agent."""
    # Check for API key
    if not OPENAI_API_KEY:
        print("Error: OPENAI_API_KEY not found in keys.py")
        print("Please add your OpenAI API key to keys.py")
        return
    
    # Initialize the agent
    agent = PicarXAgent()
    
    print("Picar-X Agent Example")
    print("=" * 50)
    
    # Example 1: Simple movement
    print("\nExample 1: Simple movement")
    print("Agent: ", end="", flush=True)
    result = Runner.run_sync(agent.agent, "Drive forward at speed 30 for 2 seconds")
    print(result.final_output)
    
    # Example 2: Sensor reading
    print("\nExample 2: Sensor reading")
    print("Agent: ", end="", flush=True)
    result = Runner.run_sync(agent.agent, "What's the distance from the ultrasonic sensor?")
    print(result.final_output)
    
    # Example 3: Complex task
    print("\nExample 3: Complex task")
    print("Agent: ", end="", flush=True)
    result = Runner.run_sync(agent.agent, "Turn the camera to look left, then take a picture")
    print(result.final_output)
    
    # Example 4: Safety demonstration
    print("\nExample 4: Safety demonstration")
    print("Agent: ", end="", flush=True)
    result = Runner.run_sync(agent.agent, "Stop the robot and reset all servos")
    print(result.final_output)
    
    print("\nExample completed.")

if __name__ == "__main__":
    main() 