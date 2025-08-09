"""
picarx_agent_advanced.py

Advanced OpenAI Agents SDK agent for controlling SunFounder Picar-X robot.
This version supports long-form tasks with memory, planning, and iterative decision making.
"""

import os
import sys
from typing import List, Optional, Dict, Any
from agents import Agent, Runner
from agents import function_tool
from agents.memory import SQLiteSession
import time
import json
import base64
from PIL import Image
import io

# Import the primitives and keys
from picarx_primitives import *
from keys import OPENAI_API_KEY

# Global variables for task state
current_task = None
task_plan = []
current_step = 0
task_history = []

# Standalone tool functions
@function_tool
def reset_tool() -> str:
    """Reset all servos to 0 and stop the motors."""
    try:
        reset()
        return "Robot reset: all servos to 0, motors stopped"
    except Exception as e:
        return f"Error resetting robot: {str(e)}"

@function_tool
def set_dir_servo_tool(angle: float) -> str:
    """Set the direction (steering) servo angle (-30 to 30 typical)."""
    try:
        set_dir_servo(angle)
        return f"Direction servo set to {angle} degrees"
    except Exception as e:
        return f"Error setting direction servo: {str(e)}"

@function_tool
def set_cam_pan_servo_tool(angle: float) -> str:
    """Set the camera pan servo angle (-35 to 35 typical)."""
    try:
        set_cam_pan_servo(angle)
        return f"Camera pan servo set to {angle} degrees"
    except Exception as e:
        return f"Error setting camera pan servo: {str(e)}"

@function_tool
def set_cam_tilt_servo_tool(angle: float) -> str:
    """Set the camera tilt servo angle (-35 to 35 typical)."""
    try:
        set_cam_tilt_servo(angle)
        return f"Camera tilt servo set to {angle} degrees"
    except Exception as e:
        return f"Error setting camera tilt servo: {str(e)}"

@function_tool
def set_motor_speed_tool(motor_id: int, speed: int) -> str:
    """Set the speed of an individual motor. motor_id: 1 (left), 2 (right), speed: -100 to 100."""
    try:
        set_motor_speed(motor_id, speed)
        return f"Motor {motor_id} speed set to {speed}"
    except Exception as e:
        return f"Error setting motor speed: {str(e)}"

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
def drive_backward_tool(speed: int, duration: Optional[float] = None) -> str:
    """Drive backward at given speed (0-100). If duration is set, drive for that many seconds then stop."""
    try:
        drive_backward(speed, duration)
        if duration:
            return f"Drove backward at speed {speed} for {duration} seconds"
        else:
            return f"Started driving backward at speed {speed}"
    except Exception as e:
        return f"Error driving backward: {str(e)}"

@function_tool
def stop_tool() -> str:
    """Stop all motors."""
    try:
        stop()
        return "Robot stopped"
    except Exception as e:
        return f"Error stopping robot: {str(e)}"

@function_tool
def turn_left_tool(angle: float, speed: int = 30, duration: Optional[float] = None) -> str:
    """Turn left by setting steering angle and driving forward. Optionally for a duration."""
    try:
        turn_left(angle, speed, duration)
        if duration:
            return f"Turned left {angle} degrees at speed {speed} for {duration} seconds"
        else:
            return f"Started turning left {angle} degrees at speed {speed}"
    except Exception as e:
        return f"Error turning left: {str(e)}"

@function_tool
def turn_right_tool(angle: float, speed: int = 30, duration: Optional[float] = None) -> str:
    """Turn right by setting steering angle and driving forward. Optionally for a duration."""
    try:
        turn_right(angle, speed, duration)
        if duration:
            return f"Turned right {angle} degrees at speed {speed} for {duration} seconds"
        else:
            return f"Started turning right {angle} degrees at speed {speed}"
    except Exception as e:
        return f"Error turning right: {str(e)}"

@function_tool
def get_ultrasound_tool() -> str:
    """Get distance in centimeters from the ultrasonic sensor."""
    try:
        distance = get_ultrasound()
        return f"Ultrasonic distance: {distance:.1f} cm"
    except Exception as e:
        return f"Error getting ultrasound distance: {str(e)}"

@function_tool
def get_grayscale_tool() -> str:
    """Get grayscale sensor readings (0-4095, left to right)."""
    try:
        values = get_grayscale()
        return f"Grayscale sensor values: {values}"
    except Exception as e:
        return f"Error getting grayscale values: {str(e)}"

@function_tool
def capture_image_tool(filename: str = "img_capture.jpg") -> str:
    """Capture an image from the camera and save to filename."""
    try:
        capture_image(filename)
        return f"Image captured and saved as {filename}"
    except Exception as e:
        return f"Error capturing image: {str(e)}"

@function_tool
def init_camera_tool() -> str:
    """Initialize the camera system for image capture."""
    try:
        init_camera()
        return "Camera system initialized successfully"
    except Exception as e:
        return f"Error initializing camera: {str(e)}"

@function_tool
def get_servo_angles_tool() -> str:
    """Get the current angles of all servos."""
    try:
        angles = get_servo_angles()
        return f"Current servo angles: Steering={angles['dir_servo']}°, Camera Pan={angles['cam_pan']}°, Camera Tilt={angles['cam_tilt']}°"
    except Exception as e:
        return f"Error getting servo angles: {str(e)}"

@function_tool
def scan_360_tool(num_photos: int = 8) -> str:
    """Perform a 360-degree scan while stationary, taking photos at different angles."""
    try:
        photo_files = scan_360_degrees(num_photos)
        return f"360-degree scan completed. Captured {len(photo_files)} photos: {', '.join(photo_files)}"
    except Exception as e:
        return f"Error during 360 scan: {str(e)}"

@function_tool
def move_backward_safe_tool(distance_cm: float = 20, speed: int = 30) -> str:
    """Move backward safely for a specified distance in centimeters."""
    try:
        success = move_backward_safe(distance_cm, speed)
        if success:
            return f"Moved backward {distance_cm}cm at speed {speed}"
        else:
            return "Failed to move backward safely"
    except Exception as e:
        return f"Error moving backward: {str(e)}"

@function_tool
def assess_environment_tool() -> str:
    """Take a photo and get sensor readings to assess the current environment."""
    try:
        assessment = assess_environment()
        result = f"Environment Assessment:\n"
        result += f"- Distance to obstacle: {assessment['distance_cm']:.1f}cm\n"
        result += f"- Current servo angles: {assessment['servo_angles']}\n"
        result += f"- Photo saved as: {assessment['photo_filename']}\n"
        
        if assessment['too_close']:
            result += "- WARNING: Too close to obstacle (< 15cm)\n"
        elif assessment['safe_distance']:
            result += "- Safe distance from obstacles\n"
        else:
            result += "- Moderate distance from obstacles\n"
            
        return result
    except Exception as e:
        return f"Error assessing environment: {str(e)}"

@function_tool
def analyze_image_tool(filename: str = "img_capture.jpg") -> str:
    """Analyze the captured image to identify obstacles, exits, paths, and objects."""
    try:
        # For now, return a basic analysis
        # In a real implementation, you might use computer vision or send to GPT-4V
        return f"Analyzing image {filename}... Image captured successfully. Use visual inspection to identify obstacles, exits, and navigable paths."
    except Exception as e:
        return f"Error analyzing image: {str(e)}"

@function_tool
def play_sound_tool(filename: str, volume: int = 100) -> str:
    """Play a sound file through the robot's speaker."""
    try:
        play_sound(filename, volume)
        return f"Playing sound file {filename} at volume {volume}"
    except Exception as e:
        return f"Error playing sound: {str(e)}"

@function_tool
def create_plan_tool(task_description: str) -> str:
    """Create a multi-step plan for a complex task."""
    global current_task, task_plan, current_step, task_history
    try:
        current_task = task_description
        task_plan = []
        current_step = 0
        task_history = []
        
        # Create a basic plan based on task type
        if "escape" in task_description.lower() or "room" in task_description.lower():
            task_plan = [
                "1. Assess current environment with photo and sensors",
                "2. If too close to obstacles, move backward to safe distance",
                "3. Perform 360-degree scan while stationary to find exits",
                "4. Analyze all photos to identify best exit route",
                "5. Execute first movement toward exit",
                "6. Reassess environment after movement",
                "7. Continue step-by-step with constant reassessment",
                "8. Adapt route if obstacles are encountered"
            ]
        elif "explore" in task_description.lower():
            task_plan = [
                "1. Take initial picture",
                "2. Systematically scan the area",
                "3. Move to interesting locations",
                "4. Document findings with pictures",
                "5. Return to starting position"
            ]
        else:
            task_plan = [
                "1. Assess current situation",
                "2. Execute task step by step",
                "3. Monitor progress",
                "4. Complete task"
            ]
        
        return f"Plan created for: {task_description}\nSteps:\n" + "\n".join(task_plan)
    except Exception as e:
        return f"Error creating plan: {str(e)}"

@function_tool
def execute_plan_step_tool(step_number: Optional[int] = None) -> str:
    """Execute the next step in the current plan."""
    global current_step, task_history
    try:
        if not task_plan:
            return "No plan available. Create a plan first."
        
        if step_number is None:
            step_number = current_step + 1
        
        if step_number > len(task_plan):
            return "All plan steps completed!"
        
        step = task_plan[step_number - 1]
        current_step = step_number
        
        # Execute the step based on its content
        if "picture" in step.lower() or "assess" in step.lower():
            result = assess_environment_tool()
            task_history.append(f"Step {step_number}: {result}")
            return f"Executed step {step_number}: {step}\nResult: {result}"
        elif "distance" in step.lower():
            result = get_ultrasound_tool()
            task_history.append(f"Step {step_number}: {result}")
            return f"Executed step {step_number}: {step}\nResult: {result}"
        elif "look around" in step.lower() or "360" in step.lower():
            # Perform 360 degree scan while stationary
            result = scan_360_tool(8)
            task_history.append(f"Step {step_number}: {result}")
            return f"Executed step {step_number}: {step}\nResult: {result}"
        elif "move" in step.lower() and "backward" in step.lower():
            result = move_backward_safe_tool(20, 25)
            # Assess environment after movement
            assessment = assess_environment_tool()
            result += f"\nPost-movement assessment: {assessment}"
            task_history.append(f"Step {step_number}: {result}")
            return f"Executed step {step_number}: {step}\nResult: {result}"
        else:
            result = f"Step {step_number} ready for execution"
            task_history.append(f"Step {step_number}: {result}")
            return f"Step {step_number}: {step}\nStatus: {result}"
            
    except Exception as e:
        return f"Error executing plan step: {str(e)}"

@function_tool
def get_task_status_tool() -> str:
    """Get the current status of the ongoing task."""
    global current_task, task_plan, current_step, task_history
    try:
        if not current_task:
            return "No active task."
        
        status = f"Current Task: {current_task}\n"
        status += f"Progress: {current_step}/{len(task_plan)} steps completed\n"
        status += f"Current Step: {task_plan[current_step - 1] if current_step > 0 else 'Not started'}\n"
        status += f"History: {len(task_history)} actions taken"
        
        return status
    except Exception as e:
        return f"Error getting task status: {str(e)}"

def create_advanced_agent():
    """Create the advanced Picar-X agent with tools."""
    # Set the API key
    os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
    
    # Create session for memory
    session = SQLiteSession(
        session_id="picarx_advanced_session",
        db_path="picarx_advanced_memory.db"
    )
    
    # Create the agent with tools
    agent = Agent(
        name="Picar-X Advanced Robot Controller",
        instructions="""You are an advanced robot controller that can perform complex, multi-step tasks with environmental awareness.
        
        You have access to the following capabilities:
        - Movement: drive_forward, drive_backward, turn_left, turn_right, stop, move_backward_safe
        - Servos: set_dir_servo (steering), set_cam_pan_servo, set_cam_tilt_servo, get_servo_angles
        - Sensors: get_ultrasound (distance), get_grayscale (line following)
        - Camera: init_camera, capture_image, scan_360 (360° scan while stationary), assess_environment
        - Audio: play_sound
        - Planning: create_plan, execute_plan_step
        
        IMPORTANT BEHAVIORS:
        1. Always check servo angles before adjusting them using get_servo_angles_tool
        2. For 360° scanning, use scan_360_tool which keeps the robot stationary
        3. After every movement, use assess_environment_tool to take a photo and check sensors
        4. If distance sensor shows < 15cm, consider moving backward using move_backward_safe_tool
        5. Take photos frequently to reassess the environment
        
        For complex tasks like "escape this room":
        1. Initialize the camera system if not already done
        2. Assess current environment (photo + sensors)
        3. If too close to obstacles, move backward to safe distance
        4. Perform 360° scan while stationary to find exits
        5. Plan path based on visual and sensor data
        6. Execute movement step by step, reassessing after each move
        7. Adapt plan based on new observations
        
        Always prioritize safety and environmental awareness.
        Take photos after every significant movement to stay oriented.""",
        tools=[
            reset_tool,
            set_dir_servo_tool,
            set_cam_pan_servo_tool,
            set_cam_tilt_servo_tool,
            set_motor_speed_tool,
            drive_forward_tool,
            drive_backward_tool,
            stop_tool,
            turn_left_tool,
            turn_right_tool,
            get_ultrasound_tool,
            get_grayscale_tool,
            init_camera_tool,
            capture_image_tool,
            get_servo_angles_tool,
            scan_360_tool,
            move_backward_safe_tool,
            assess_environment_tool,
            analyze_image_tool,
            play_sound_tool,
            create_plan_tool,
            execute_plan_step_tool,
            get_task_status_tool
        ]
    )
    return agent, session

def execute_long_form_task(agent, session, task_description: str) -> str:
    """Execute a long-form task with planning and iteration."""
    try:
        # Create a plan
        plan_result = Runner.run_sync(agent, f"Create a plan for: {task_description}", session=session)
        print(f"Plan created: {plan_result.final_output}")
        
        # Execute the plan step by step
        while current_step < len(task_plan):
            step_result = Runner.run_sync(agent, f"Execute the next step in the plan", session=session)
            print(f"Step {current_step + 1}: {step_result.final_output}")
            
            # Check if we need to adapt the plan
            if "obstacle" in step_result.final_output.lower() or "blocked" in step_result.final_output.lower():
                adapt_result = Runner.run_sync(agent, "The path is blocked. Adapt the plan to find an alternative route.", session=session)
                print(f"Plan adapted: {adapt_result.final_output}")
        
        # Get final status
        status_result = Runner.run_sync(agent, "Get the final task status", session=session)
        return status_result.final_output
        
    except Exception as e:
        return f"Error executing long-form task: {str(e)}"

def main():
    """Main function to run the advanced Picar-X agent."""
    # Check for API key
    if not OPENAI_API_KEY:
        print("Error: OPENAI_API_KEY not found in keys.py")
        print("Please add your OpenAI API key to keys.py")
        sys.exit(1)
    
    # Initialize the agent with session
    agent, session = create_advanced_agent()
    
    print("Advanced Picar-X Agent with Memory initialized!")
    print("Type 'quit' to exit")
    print("Type 'reset' to reset the robot")
    print("Type 'status' to check task status")
    print("Type 'memory' to test memory functionality")
    print("Type 'escape room' for a complex task example")
    print("Memory is enabled - I will remember our conversations!")
    print("-" * 50)
    
    try:
        while True:
            # Get user input from keyboard
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
        print("\nExiting...")


if __name__ == "__main__":
    main() 