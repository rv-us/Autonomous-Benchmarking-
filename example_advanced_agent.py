"""
example_advanced_agent.py

Example usage of the advanced Picar-X agent for long-form tasks.
This script demonstrates complex task execution with planning and iteration.
"""

import os
from picarx_agent_advanced import PicarXAdvancedAgent
from agents import Runner
from keys import OPENAI_API_KEY

def main():
    """Example usage of the advanced Picar-X agent."""
    # Check for API key
    if not OPENAI_API_KEY:
        print("Error: OPENAI_API_KEY not found in keys.py")
        print("Please add your OpenAI API key to keys.py")
        return
    
    # Initialize the agent
    agent = PicarXAdvancedAgent()
    
    print("Advanced Picar-X Agent Example")
    print("=" * 50)
    
    # Example 1: Simple task with planning
    print("\nExample 1: Create a plan for exploring the room")
    print("Agent: ", end="", flush=True)
    result = Runner.run_sync(agent.agent, "Create a plan for exploring this room")
    print(result.final_output)
    
    # Example 2: Execute plan steps
    print("\nExample 2: Execute the first step of the plan")
    print("Agent: ", end="", flush=True)
    result = Runner.run_sync(agent.agent, "Execute the next step in the plan")
    print(result.final_output)
    
    # Example 3: Check task status
    print("\nExample 3: Check current task status")
    print("Agent: ", end="", flush=True)
    result = Runner.run_sync(agent.agent, "Get the current task status")
    print(result.final_output)
    
    # Example 4: Complex task execution
    print("\nExample 4: Execute a complex task (escape room)")
    print("Agent: ", end="", flush=True)
    result = agent.execute_long_form_task("Escape this room by finding the exit and navigating to it")
    print(result)
    
    print("\nAdvanced example completed.")

if __name__ == "__main__":
    main() 