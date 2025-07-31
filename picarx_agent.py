"""
picarx_agent.py

OpenAI Agents SDK agent for controlling SunFounder Picar-X robot.
This agent uses the functions from picarx_primitives.py as tools.
"""

import os
import sys
from typing import List, Optional
from agents import Agent, Runner, tool
import time
import json

# Import the primitives and keys
from picarx_primitives import *
from keys import OPENAI_API_KEY

class PicarXAgent:
    def __init__(self, api_key: str = None):
        """Initialize the Picar-X agent with OpenAI API key."""
        # Use provided API key or get from keys.py
        if api_key is None:
            api_key = OPENAI_API_KEY
        
        # Set the API key
        os.environ["OPENAI_API_KEY"] = api_key
        
        # Create the agent with tools
        self.agent = Agent(
            name="Picar-X Robot Controller",
            instructions="""You are a helpful assistant that controls a SunFounder Picar-X robot. 
            You can control the robot's movement, servos, sensors, camera, and speaker.
            
            Available actions:
            - Movement: drive_forward, drive_backward, turn_left, turn_right, stop
            - Servos: set_dir_servo (steering), set_cam_pan_servo, set_cam_tilt_servo
            - Sensors: get_ultrasound (distance), get_grayscale (line following)
            - Camera: capture_image
            - Audio: play_sound
            
            Always be careful with movement commands and consider safety. 
            Use appropriate speeds and durations for smooth operation.
            When asked to perform complex tasks, break them down into simple steps.""",
            tools=[
                self.reset_tool,
                self.set_dir_servo_tool,
                self.set_cam_pan_servo_tool,
                self.set_cam_tilt_servo_tool,
                self.set_motor_speed_tool,
                self.drive_forward_tool,
                self.drive_backward_tool,
                self.stop_tool,
                self.turn_left_tool,
                self.turn_right_tool,
                self.get_ultrasound_tool,
                self.get_grayscale_tool,
                self.capture_image_tool,
                self.play_sound_tool
            ]
        )
    
    @tool
    def reset_tool(self) -> str:
        """Reset all servos to 0 and stop the motors."""
        try:
            reset()
            return "Robot reset: all servos to 0, motors stopped"
        except Exception as e:
            return f"Error resetting robot: {str(e)}"
    
    @tool
    def set_dir_servo_tool(self, angle: float) -> str:
        """Set the direction (steering) servo angle (-30 to 30 typical)."""
        try:
            set_dir_servo(angle)
            return f"Direction servo set to {angle} degrees"
        except Exception as e:
            return f"Error setting direction servo: {str(e)}"
    
    @tool
    def set_cam_pan_servo_tool(self, angle: float) -> str:
        """Set the camera pan servo angle (-35 to 35 typical)."""
        try:
            set_cam_pan_servo(angle)
            return f"Camera pan servo set to {angle} degrees"
        except Exception as e:
            return f"Error setting camera pan servo: {str(e)}"
    
    @tool
    def set_cam_tilt_servo_tool(self, angle: float) -> str:
        """Set the camera tilt servo angle (-35 to 35 typical)."""
        try:
            set_cam_tilt_servo(angle)
            return f"Camera tilt servo set to {angle} degrees"
        except Exception as e:
            return f"Error setting camera tilt servo: {str(e)}"
    
    @tool
    def set_motor_speed_tool(self, motor_id: int, speed: int) -> str:
        """Set the speed of an individual motor. motor_id: 1 (left), 2 (right), speed: -100 to 100."""
        try:
            set_motor_speed(motor_id, speed)
            return f"Motor {motor_id} speed set to {speed}"
        except Exception as e:
            return f"Error setting motor speed: {str(e)}"
    
    @tool
    def drive_forward_tool(self, speed: int, duration: Optional[float] = None) -> str:
        """Drive forward at given speed (0-100). If duration is set, drive for that many seconds then stop."""
        try:
            drive_forward(speed, duration)
            if duration:
                return f"Drove forward at speed {speed} for {duration} seconds"
            else:
                return f"Started driving forward at speed {speed}"
        except Exception as e:
            return f"Error driving forward: {str(e)}"
    
    @tool
    def drive_backward_tool(self, speed: int, duration: Optional[float] = None) -> str:
        """Drive backward at given speed (0-100). If duration is set, drive for that many seconds then stop."""
        try:
            drive_backward(speed, duration)
            if duration:
                return f"Drove backward at speed {speed} for {duration} seconds"
            else:
                return f"Started driving backward at speed {speed}"
        except Exception as e:
            return f"Error driving backward: {str(e)}"
    
    @tool
    def stop_tool(self) -> str:
        """Stop all motors."""
        try:
            stop()
            return "Robot stopped"
        except Exception as e:
            return f"Error stopping robot: {str(e)}"
    
    @tool
    def turn_left_tool(self, angle: float, speed: int = 30, duration: Optional[float] = None) -> str:
        """Turn left by setting steering angle and driving forward. Optionally for a duration."""
        try:
            turn_left(angle, speed, duration)
            if duration:
                return f"Turned left {angle} degrees at speed {speed} for {duration} seconds"
            else:
                return f"Started turning left {angle} degrees at speed {speed}"
        except Exception as e:
            return f"Error turning left: {str(e)}"
    
    @tool
    def turn_right_tool(self, angle: float, speed: int = 30, duration: Optional[float] = None) -> str:
        """Turn right by setting steering angle and driving forward. Optionally for a duration."""
        try:
            turn_right(angle, speed, duration)
            if duration:
                return f"Turned right {angle} degrees at speed {speed} for {duration} seconds"
            else:
                return f"Started turning right {angle} degrees at speed {speed}"
        except Exception as e:
            return f"Error turning right: {str(e)}"
    
    @tool
    def get_ultrasound_tool(self) -> str:
        """Get distance in centimeters from the ultrasonic sensor."""
        try:
            distance = get_ultrasound()
            return f"Ultrasonic distance: {distance:.1f} cm"
        except Exception as e:
            return f"Error getting ultrasound distance: {str(e)}"
    
    @tool
    def get_grayscale_tool(self) -> str:
        """Get grayscale sensor readings (0-4095, left to right)."""
        try:
            values = get_grayscale()
            return f"Grayscale sensor values: {values}"
        except Exception as e:
            return f"Error getting grayscale values: {str(e)}"
    
    @tool
    def capture_image_tool(self, filename: str = "img_capture.jpg") -> str:
        """Capture an image from the camera and save to filename. Requires Vilib to be running."""
        try:
            capture_image(filename)
            return f"Image captured and saved as {filename}"
        except Exception as e:
            return f"Error capturing image: {str(e)}"
    
    @tool
    def play_sound_tool(self, filename: str, volume: int = 100) -> str:
        """Play a sound file through the robot's speaker."""
        try:
            play_sound(filename, volume)
            return f"Playing sound file {filename} at volume {volume}"
        except Exception as e:
            return f"Error playing sound: {str(e)}"
    
    def send_message(self, message: str):
        """Send a message to the agent and get a response."""
        try:
            result = Runner.run_sync(self.agent, message)
            return result.final_output
        except Exception as e:
            return f"Error running agent: {str(e)}"


def main():
    """Main function to run the Picar-X agent."""
    # Check for API key
    if not OPENAI_API_KEY:
        print("Error: OPENAI_API_KEY not found in keys.py")
        print("Please add your OpenAI API key to keys.py")
        sys.exit(1)
    
    # Initialize the agent
    agent = PicarXAgent()
    
    print("Picar-X Agent initialized!")
    print("Type 'quit' to exit")
    print("Type 'reset' to reset the robot")
    print("-" * 50)
    
    try:
        while True:
            # Get user input from keyboard
            user_input = input("You: ").strip()
            
            if user_input.lower() == 'quit':
                break
            elif user_input.lower() == 'reset':
                result = Runner.run_sync(agent.agent, "Reset the robot")
                print(f"Agent: {result.final_output}")
                continue
            
            # Send message to agent
            print("Agent: ", end="", flush=True)
            response = agent.send_message(user_input)
            print(response)
            print()
            
    except KeyboardInterrupt:
        print("\nExiting...")


if __name__ == "__main__":
    main() 