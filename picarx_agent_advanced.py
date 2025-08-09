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
    """Capture an image from the camera and save to filename. Requires Vilib to be running."""
    try:
        capture_image(filename)
        return f"Image captured and saved as {filename}"
    except Exception as e:
        return f"Error capturing image: {str(e)}"

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
                "1. Take initial picture to assess environment",
                "2. Check distance to obstacles",
                "3. Look around 360 degrees to find exits",
                "4. Plan path to exit",
                "5. Execute movement while avoiding obstacles",
                "6. Verify progress and adjust if needed"
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
        if "picture" in step.lower():
            result = capture_image_tool()
            task_history.append(f"Step {step_number}: {result}")
            return f"Executed step {step_number}: {step}\nResult: {result}"
        elif "distance" in step.lower():
            result = get_ultrasound_tool()
            task_history.append(f"Step {step_number}: {result}")
            return f"Executed step {step_number}: {step}\nResult: {result}"
        elif "look around" in step.lower():
            # Pan camera to look around
            set_cam_pan_servo_tool(-30)
            time.sleep(1)
            set_cam_pan_servo_tool(30)
            time.sleep(1)
            set_cam_pan_servo_tool(0)
            result = "Looked around 360 degrees"
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
    
    # Create the agent with tools
    agent = Agent(
        name="Picar-X Advanced Robot Controller",
        instructions="""You are an advanced robot controller that can perform complex, multi-step tasks.
        
        You have access to the following capabilities:
        - Movement: drive_forward, drive_backward, turn_left, turn_right, stop
        - Servos: set_dir_servo (steering), set_cam_pan_servo, set_cam_tilt_servo
        - Sensors: get_ultrasound (distance), get_grayscale (line following)
        - Camera: capture_image, analyze_image
        - Audio: play_sound
        - Planning: create_plan, execute_plan_step
        
        For complex tasks like "escape this room":
        1. First create a plan with multiple steps
        2. Execute each step while monitoring progress
        3. Adapt the plan based on what you observe
        4. Use sensor data and images to make decisions
        5. Continue until the task is complete
        
        Always prioritize safety and be careful with movement commands.
        Use appropriate speeds and durations for smooth operation.
        When analyzing images, look for obstacles, exits, and navigable paths.""",
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
            capture_image_tool,
            analyze_image_tool,
            play_sound_tool,
            create_plan_tool,
            execute_plan_step_tool,
            get_task_status_tool
        ]
    )
    return agent

def execute_long_form_task(agent, task_description: str) -> str:
    """Execute a long-form task with planning and iteration."""
    try:
        # Create a plan
        plan_result = Runner.run_sync(agent, f"Create a plan for: {task_description}")
        print(f"Plan created: {plan_result.final_output}")
        
        # Execute the plan step by step
        while current_step < len(task_plan):
            step_result = Runner.run_sync(agent, f"Execute the next step in the plan")
            print(f"Step {current_step + 1}: {step_result.final_output}")
            
            # Check if we need to adapt the plan
            if "obstacle" in step_result.final_output.lower() or "blocked" in step_result.final_output.lower():
                adapt_result = Runner.run_sync(agent, "The path is blocked. Adapt the plan to find an alternative route.")
                print(f"Plan adapted: {adapt_result.final_output}")
        
        # Get final status
        status_result = Runner.run_sync(agent, "Get the final task status")
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
    
    # Initialize the agent
    agent = create_advanced_agent()
    
    print("Advanced Picar-X Agent initialized!")
    print("Type 'quit' to exit")
    print("Type 'reset' to reset the robot")
    print("Type 'status' to check task status")
    print("Type 'escape room' for a complex task example")
    print("-" * 50)
    
    try:
        while True:
            # Get user input from keyboard
            user_input = input("You: ").strip()
            
            if user_input.lower() == 'quit':
                break
            elif user_input.lower() == 'reset':
                result = Runner.run_sync(agent, "Reset the robot")
                print(f"Agent: {result.final_output}")
                continue
            elif user_input.lower() == 'status':
                result = Runner.run_sync(agent, "Get the current task status")
                print(f"Agent: {result.final_output}")
                continue
            elif "escape" in user_input.lower() or "room" in user_input.lower():
                print("Agent: Starting complex task execution...")
                result = execute_long_form_task(agent, user_input)
                print(f"Agent: {result}")
                continue
            
            # Send message to agent
            print("Agent: ", end="", flush=True)
            try:
                result = Runner.run_sync(agent, user_input)
                print(result.final_output)
            except Exception as e:
                print(f"Error getting response: {str(e)}")
            print()
            
    except KeyboardInterrupt:
        print("\nExiting...")


if __name__ == "__main__":
    main() 