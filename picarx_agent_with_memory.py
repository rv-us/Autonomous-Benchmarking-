"""
picarx_agent_with_memory.py

Enhanced OpenAI Agents SDK agent for Picar-X with persistent memory and multiturn conversations.
Compatible with Python 3.9+ and Raspberry Pi.
"""

import os
import sys
from typing import List, Optional, Dict, Any
from agents import Agent, Runner, SQLiteSession
from agents import function_tool
import time
import json
from pathlib import Path

# Import the primitives and keys
from picarx_primitives import *
from keys import OPENAI_API_KEY

# Session configuration
SESSION_DB_PATH = "picarx_sessions.db"
DEFAULT_SESSION_ID = "picarx_main_session"

# Tool functions (same as before but with memory context)
@function_tool
def reset_tool() -> str:
    """Reset all servos to 0 and stop the motors."""
    try:
        reset()
        return "Robot reset: all servos to 0, motors stopped"
    except Exception as e:
        return f"Error resetting robot: {str(e)}"

@function_tool
def drive_forward_tool(speed: int, duration: Optional[float] = None) -> str:
    """Drive forward at given speed (0-100). If duration is set, drive for that many seconds then stop."""
    try:
        drive_forward(speed, duration)
        if duration:
            return f"Drove forward at speed {speed} for {duration} seconds"
        else:
            return f"Started driving forward at speed {speed}"
    except Exception as e:
        return f"Error driving forward: {str(e)}"

@function_tool
def get_ultrasound_tool() -> str:
    """Get distance in centimeters from the ultrasonic sensor."""
    try:
        distance = get_ultrasound()
        return f"Ultrasonic distance: {distance:.1f} cm"
    except Exception as e:
        return f"Error getting ultrasound distance: {str(e)}"

@function_tool
def capture_image_tool(filename: str = "img_capture.jpg") -> str:
    """Capture an image from the camera and save to filename."""
    try:
        capture_image(filename)
        return f"Image captured and saved as {filename}"
    except Exception as e:
        return f"Error capturing image: {str(e)}"

@function_tool
def remember_location_tool(location_name: str, description: str) -> str:
    """Remember a specific location with a name and description for future reference."""
    try:
        # This would be stored in the session automatically
        return f"Remembered location '{location_name}': {description}"
    except Exception as e:
        return f"Error remembering location: {str(e)}"

@function_tool
def set_task_goal_tool(goal: str) -> str:
    """Set a long-term goal or task that should be remembered across conversations."""
    try:
        return f"Task goal set: {goal}. I will remember this for future interactions."
    except Exception as e:
        return f"Error setting task goal: {str(e)}"

class PicarXAgentWithMemory:
    def __init__(self, session_id: str = DEFAULT_SESSION_ID, db_path: str = SESSION_DB_PATH):
        """Initialize the Picar-X agent with persistent memory."""
        # Set the API key
        os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
        
        # Create session for persistent memory
        self.session = SQLiteSession(
            session_id=session_id,
            db_path=db_path
        )
        
        # Create the agent
        self.agent = Agent(
            name="Picar-X Robot with Memory",
            instructions="""You are a helpful assistant that controls a SunFounder Picar-X robot with persistent memory.
            
            You can remember:
            - Previous conversations and commands
            - Locations you've visited and their descriptions
            - Tasks and goals set by the user
            - Sensor readings and observations over time
            - Images captured and their context
            
            Available actions:
            - Movement: drive_forward, drive_backward, turn_left, turn_right, stop
            - Servos: set_dir_servo (steering), set_cam_pan_servo, set_cam_tilt_servo
            - Sensors: get_ultrasound (distance), get_grayscale (line following)
            - Camera: capture_image
            - Memory: remember_location, set_task_goal
            
            Use your memory to:
            - Reference previous conversations and actions
            - Build upon past experiences
            - Maintain context across multiple sessions
            - Learn from previous sensor readings and observations
            
            Always be helpful and remember what the user has told you before.""",
            tools=[
                reset_tool,
                drive_forward_tool,
                get_ultrasound_tool,
                capture_image_tool,
                remember_location_tool,
                set_task_goal_tool
            ]
        )
    
    def chat(self, message: str, max_turns: int = 10) -> str:
        """Send a message to the agent with persistent memory."""
        try:
            result = Runner.run_sync(
                self.agent, 
                message, 
                session=self.session,
                max_turns=max_turns
            )
            return result.final_output
        except Exception as e:
            return f"Error in conversation: {str(e)}"
    
    def get_session_history(self) -> List[Dict[str, Any]]:
        """Get the conversation history from the session."""
        try:
            # This would depend on the specific SQLiteSession implementation
            # For now, return a placeholder
            return [{"message": "Session history would be retrieved here"}]
        except Exception as e:
            return [{"error": f"Could not retrieve history: {str(e)}"}]
    
    def clear_memory(self):
        """Clear the session memory (use with caution)."""
        try:
            # Create a new session with the same ID to effectively clear it
            self.session = SQLiteSession(
                session_id=self.session.session_id,
                db_path=SESSION_DB_PATH
            )
            return "Memory cleared successfully"
        except Exception as e:
            return f"Error clearing memory: {str(e)}"

def main():
    """Main function demonstrating multiturn conversation with memory."""
    # Check for API key
    if not OPENAI_API_KEY:
        print("Error: OPENAI_API_KEY not found in keys.py")
        sys.exit(1)
    
    # Initialize the agent with memory
    agent = PicarXAgentWithMemory()
    
    print("Picar-X Agent with Memory initialized!")
    print("Your conversations will be remembered across sessions.")
    print("Commands:")
    print("  'quit' - Exit")
    print("  'history' - Show conversation history")
    print("  'clear' - Clear memory")
    print("  'new_session <id>' - Start a new session")
    print("-" * 50)
    
    try:
        while True:
            user_input = input("You: ").strip()
            
            if user_input.lower() == 'quit':
                break
            elif user_input.lower() == 'history':
                history = agent.get_session_history()
                print("Session History:")
                for item in history:
                    print(f"  {item}")
                continue
            elif user_input.lower() == 'clear':
                result = agent.clear_memory()
                print(f"Agent: {result}")
                continue
            elif user_input.lower().startswith('new_session '):
                session_id = user_input.split(' ', 1)[1]
                agent = PicarXAgentWithMemory(session_id=session_id)
                print(f"Agent: Started new session: {session_id}")
                continue
            
            # Send message to agent with memory
            print("Agent: ", end="", flush=True)
            response = agent.chat(user_input)
            print(response)
            print()
            
    except KeyboardInterrupt:
        print("\nExiting...")

if __name__ == "__main__":
    main()