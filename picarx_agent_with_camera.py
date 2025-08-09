#!/usr/bin/env python3
"""
picarx_agent_with_camera.py

Enhanced Picar-X agent that properly initializes the camera system before starting.
This version handles the vilib camera initialization correctly.
"""

import os
import sys
import time
from picarx_agent_advanced import create_advanced_agent, execute_long_form_task
from picarx_primitives import init_camera, close_camera
from agents import Runner

def main():
    """Main function with proper camera initialization."""
    print("Initializing Picar-X Agent with Camera...")
    
    try:
        # Initialize camera first
        print("Setting up camera system...")
        init_camera()
        print("Camera ready!")
        
        # Initialize the agent with session
        print("Creating agent...")
        agent, session = create_advanced_agent()
        
        print("=" * 60)
        print("Picar-X Agent with Camera & Memory Ready!")
        print("Commands:")
        print("  'quit' - Exit")
        print("  'reset' - Reset the robot")
        print("  'status' - Check task status")
        print("  'memory' - Test memory functionality")
        print("  'photo' - Take a photo")
        print("  'escape room' - Complex task example")
        print("Camera is initialized and ready for image capture!")
        print("=" * 60)
        
        try:
            while True:
                user_input = input("You: ").strip()
                
                if user_input.lower() == 'quit':
                    break
                elif user_input.lower() == 'reset':
                    result = Runner.run_sync(agent, "Reset the robot", session=session)
                    print(f"Agent: {result.final_output}")
                    continue
                elif user_input.lower() == 'status':
                    result = Runner.run_sync(agent, "Get the current task status", session=session)
                    print(f"Agent: {result.final_output}")
                    continue
                elif user_input.lower() == 'memory':
                    result = Runner.run_sync(agent, "Tell me what you remember about our previous conversations and interactions", session=session)
                    print(f"Agent: {result.final_output}")
                    continue
                elif user_input.lower() == 'photo':
                    result = Runner.run_sync(agent, "Take a photo and tell me what you see", session=session)
                    print(f"Agent: {result.final_output}")
                    continue
                elif "escape" in user_input.lower() or "room" in user_input.lower():
                    print("Agent: Starting complex task execution...")
                    result = execute_long_form_task(agent, session, user_input)
                    print(f"Agent: {result}")
                    continue
                
                # Send message to agent with session for memory
                print("Agent: ", end="", flush=True)
                try:
                    result = Runner.run_sync(agent, user_input, session=session)
                    print(result.final_output)
                except Exception as e:
                    print(f"Error getting response: {str(e)}")
                print()
                
        except KeyboardInterrupt:
            print("\nShutting down...")
            
    except Exception as e:
        print(f"Initialization error: {str(e)}")
        print("Make sure the Picar-X hardware is connected and vilib is installed.")
        
    finally:
        # Clean shutdown
        try:
            close_camera()
            print("Camera closed successfully")
        except:
            pass

if __name__ == "__main__":
    main()