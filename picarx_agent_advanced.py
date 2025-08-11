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
def turn_in_place_right_tool(degrees: float = 45) -> str:
    """Turn right in place by specified degrees (default 45°)."""
    try:
        success = turn_in_place_right(degrees)
        if success:
            return f"Turned right {degrees}° in place"
        else:
            return f"Failed to turn right {degrees}°"
    except Exception as e:
        return f"Error turning right: {str(e)}"

@function_tool
def turn_in_place_left_tool(degrees: float = 45) -> str:
    """Turn left in place by specified degrees (default 45°)."""
    try:
        success = turn_in_place_left(degrees)
        if success:
            return f"Turned left {degrees}° in place"
        else:
            return f"Failed to turn left {degrees}°"
    except Exception as e:
        return f"Error turning left: {str(e)}"

@function_tool
def check_current_direction_tool() -> str:
    """Take a photo and check ultrasound in current direction to assess if it's an exit."""
    try:
        result = check_current_direction()
        
        # Prepare context for image analysis
        context = f"""I am a Picar-X robot trying to escape from a room. I just took this photo while facing a potential exit direction.

Current sensor data:
- Ultrasonic distance: {result['distance_cm']:.1f}cm
- Sensor assessment: {result['assessment']}
- Current servo positions: {get_servo_angles()}

Please analyze this image and tell me:
1. Do you see a clear exit (doorway, opening, passage)?
2. Are there obstacles blocking the path?
3. How far ahead does the clear path extend?
4. Should I move forward, turn to look elsewhere, or back up?
5. Any safety concerns I should be aware of?

Based on your analysis, provide specific navigation instructions."""

        # Upload image with context (this would need to be implemented based on your chat system)
        upload_result = upload_image_with_context(result['photo_filename'], context)
        
        response = f"Direction Assessment:\n"
        response += f"- Photo captured: {result['photo_filename']}\n"
        response += f"- Distance: {result['distance_cm']:.1f}cm\n"
        response += f"- Status: {result['assessment']}\n"
        response += f"- Image uploaded for analysis: {upload_result}\n"
        
        if result['is_exit_candidate']:
            response += "- Sensor data suggests potential EXIT - awaiting visual confirmation\n"
        elif result['is_clear']:
            response += "- Path appears clear - awaiting visual analysis\n"
        else:
            response += "- Path blocked by sensors - visual analysis will confirm\n"
        
        return response
        
    except Exception as e:
        return f"Error checking current direction: {str(e)}"

@function_tool
def upload_image_with_context(filename: str, context: str) -> str:
    """Upload an image file with contextual information for analysis using OpenAI Agents SDK."""
    try:
        import os
        import base64
        from agents import Agent, Runner
        
        if not os.path.exists(filename):
            return f"Image file {filename} not found"
        
        # Read and encode the image
        with open(filename, "rb") as image_file:
            image_data = image_file.read()
            base64_image = base64.b64encode(image_data).decode('utf-8')
        
        # Create the message with image using OpenAI Agents SDK format
        message_with_image = [
            {
                "type": "text",
                "text": context
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{base64_image}"
                }
            }
        ]
        
        # Create a simple analysis agent for this specific image
        from keys import OPENAI_API_KEY
        
        os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
        
        analysis_agent = Agent(
            name="Robot Navigation Image Analyzer",
            instructions="""You are an expert at analyzing images for robot navigation and escape room scenarios.
            
            When given an image from a Picar-X robot, analyze it carefully and provide:
            1. What you see in the image (exits, doorways, obstacles, walls, furniture, paths)
            2. Specific navigation recommendations (move forward X cm, turn left/right Y degrees, stop, back up)
            3. Safety considerations and potential hazards
            4. Distance estimates for objects and clearances
            5. Whether this direction appears to be a viable exit
            
            Be specific, actionable, and safety-focused in your guidance. The robot needs clear instructions."""
        )
        
        # Send the image for analysis
        result = Runner.run_sync(analysis_agent, message_with_image)
        
        analysis_result = result.final_output
        
        return f"🤖 IMAGE ANALYSIS COMPLETE 🤖\n\nFile: {filename}\nAnalysis:\n{analysis_result}\n\nUse this guidance to navigate the robot safely."
        
    except Exception as e:
        return f"Error uploading and analyzing image: {str(e)}"

@function_tool
def receive_navigation_guidance_tool(guidance: str) -> str:
    """Receive navigation guidance from advanced agent analysis and execute appropriate actions."""
    try:
        guidance_lower = guidance.lower()
        
        response = f"Received navigation guidance: {guidance}\n\nExecuting recommended actions:\n"
        
        # Parse guidance and execute actions
        if "move forward" in guidance_lower or "go forward" in guidance_lower:
            # Extract distance if mentioned
            import re
            distance_match = re.search(r'(\d+)\s*(cm|centimeter)', guidance_lower)
            if distance_match:
                distance = int(distance_match.group(1))
                duration = distance / 20  # Rough conversion
                result = drive_forward_tool(30, duration)
                response += f"- {result}\n"
            else:
                result = drive_forward_tool(30, 2)  # Default 2 seconds
                response += f"- {result}\n"
                
        elif "turn right" in guidance_lower:
            # Extract degrees if mentioned
            import re
            degrees_match = re.search(r'(\d+)\s*degree', guidance_lower)
            degrees = int(degrees_match.group(1)) if degrees_match else 45
            result = turn_in_place_right_tool(degrees)
            response += f"- {result}\n"
            
        elif "turn left" in guidance_lower:
            # Extract degrees if mentioned
            import re
            degrees_match = re.search(r'(\d+)\s*degree', guidance_lower)
            degrees = int(degrees_match.group(1)) if degrees_match else 45
            result = turn_in_place_left_tool(degrees)
            response += f"- {result}\n"
            
        elif "back up" in guidance_lower or "move backward" in guidance_lower:
            # Extract distance if mentioned
            import re
            distance_match = re.search(r'(\d+)\s*(cm|centimeter)', guidance_lower)
            distance = int(distance_match.group(1)) if distance_match else 20
            result = move_backward_safe_tool(distance)
            response += f"- {result}\n"
            
        elif "stop" in guidance_lower or "wait" in guidance_lower:
            result = stop_tool()
            response += f"- {result}\n"
            
        elif "assess" in guidance_lower or "check" in guidance_lower:
            result = assess_environment_tool()
            response += f"- {result}\n"
            
        else:
            response += "- Guidance received but no specific action recognized\n"
            response += "- Available actions: move forward, turn right/left, back up, stop, assess\n"
        
        return response
        
    except Exception as e:
        return f"Error processing navigation guidance: {str(e)}"

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
        
        # Prepare context for image analysis
        context = f"""I am a Picar-X robot assessing my current environment for navigation.

Current situation:
- Ultrasonic distance: {assessment['distance_cm']:.1f}cm
- Servo positions: {assessment['servo_angles']}
- Safety status: {'TOO CLOSE' if assessment['too_close'] else 'SAFE DISTANCE' if assessment['safe_distance'] else 'MODERATE DISTANCE'}

Please analyze this environmental photo and tell me:
1. What obstacles or objects do you see around me?
2. Which directions appear to have clear paths?
3. Are there any potential exits or openings visible?
4. What should be my next navigation step?
5. Any immediate safety concerns?

Provide specific guidance for my next movement."""

        # Upload image with context
        upload_result = upload_image_with_context(assessment['photo_filename'], context)
        
        result = f"Environment Assessment:\n"
        result += f"- Distance to obstacle: {assessment['distance_cm']:.1f}cm\n"
        result += f"- Current servo angles: {assessment['servo_angles']}\n"
        result += f"- Photo captured: {assessment['photo_filename']}\n"
        result += f"- Image uploaded for analysis: {upload_result}\n"
        
        if assessment['too_close']:
            result += "- WARNING: Too close to obstacle (< 15cm) - awaiting visual guidance\n"
        elif assessment['safe_distance']:
            result += "- Safe distance from obstacles - awaiting navigation advice\n"
        else:
            result += "- Moderate distance from obstacles - awaiting visual analysis\n"
            
        return result
    except Exception as e:
        return f"Error assessing environment: {str(e)}"

@function_tool
def rotate_in_place_tool(degrees: float, speed: int = 30) -> str:
    """Rotate the robot in place. Positive degrees = clockwise, negative = counter-clockwise."""
    try:
        success = rotate_in_place(degrees, speed)
        if success:
            direction = "clockwise" if degrees > 0 else "counter-clockwise"
            return f"Rotated {abs(degrees)}° {direction} in place"
        else:
            return "Failed to rotate in place"
    except Exception as e:
        return f"Error rotating in place: {str(e)}"



@function_tool
def analyze_image_tool(filename: str = "img_capture.jpg") -> str:
    """Save image for manual analysis via file upload."""
    try:
        import os
        if os.path.exists(filename):
            return f"Image {filename} captured and saved. Please upload this file to analyze what the robot sees for navigation guidance."
        else:
            return f"Image file {filename} not found"
    except Exception as e:
        return f"Error with image {filename}: {str(e)}"

@function_tool
def prepare_analysis_report_tool() -> str:
    """Generate a comprehensive report of sensor data and images for external analysis."""
    try:
        import glob
        import os
        from datetime import datetime
        
        # Find all recent scan photos
        scan_photos = glob.glob("scan_360_*.jpg")
        other_photos = glob.glob("img_capture*.jpg") + glob.glob("assessment_*.jpg")
        
        # Sort by modification time to get most recent
        all_photos = scan_photos + other_photos
        if all_photos:
            all_photos.sort(key=os.path.getmtime, reverse=True)
        
        # Get current sensor readings
        distance = get_ultrasound()
        servo_angles = get_servo_angles()
        
        # Generate comprehensive report
        report = f"=== PICAR-X NAVIGATION ANALYSIS REQUEST ===\n"
        report += f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        report += f"CURRENT SENSOR DATA:\n"
        report += f"- Ultrasonic Distance: {distance:.1f}cm\n"
        report += f"- Servo Positions: Steering={servo_angles['dir_servo']}°, "
        report += f"Camera Pan={servo_angles['cam_pan']}°, Camera Tilt={servo_angles['cam_tilt']}°\n\n"
        
        if scan_photos:
            report += f"360° SCAN IMAGES (upload these for directional analysis):\n"
            directions = ['north', 'east', 'south', 'west']
            for direction in directions:
                direction_photos = [p for p in scan_photos if direction in p.lower()]
                if direction_photos:
                    latest_photo = max(direction_photos, key=os.path.getmtime)
                    report += f"- {direction.upper()}: {latest_photo}\n"
        
        if other_photos:
            report += f"\nOTHER RECENT IMAGES:\n"
            for photo in other_photos[:5]:  # Show up to 5 most recent
                report += f"- {photo}\n"
        
        report += f"\nANALYSIS REQUEST:\n"
        report += f"Please upload the images above and provide:\n"
        report += f"1. Visual analysis of each direction (exits, obstacles, clear paths)\n"
        report += f"2. Best exit direction recommendation\n"
        report += f"3. Navigation instructions (rotate degrees, move distance)\n"
        report += f"4. Safety considerations and obstacles to avoid\n"
        
        return report
        
    except Exception as e:
        return f"Error generating analysis report: {str(e)}"

@function_tool
def execute_navigation_command_tool(command: str) -> str:
    """Execute a navigation command received from external analysis."""
    try:
        command = command.lower().strip()
        
        if "rotate" in command and "clockwise" in command:
            # Extract degrees if specified
            import re
            degrees_match = re.search(r'(\d+)', command)
            degrees = int(degrees_match.group(1)) if degrees_match else 90
            return rotate_in_place_tool(degrees)
            
        elif "rotate" in command and ("counter" in command or "left" in command):
            # Extract degrees if specified
            import re
            degrees_match = re.search(r'(\d+)', command)
            degrees = int(degrees_match.group(1)) if degrees_match else 90
            return rotate_in_place_tool(-degrees)
            
        elif "move forward" in command or "drive forward" in command:
            # Extract distance/duration if specified
            import re
            distance_match = re.search(r'(\d+)', command)
            if distance_match:
                duration = int(distance_match.group(1)) / 10  # Convert cm to rough duration
                return drive_forward_tool(30, duration)
            else:
                return drive_forward_tool(30, 2)  # Default 2 seconds
                
        elif "move backward" in command or "back up" in command:
            import re
            distance_match = re.search(r'(\d+)', command)
            distance = int(distance_match.group(1)) if distance_match else 20
            return move_backward_safe_tool(distance)
            
        elif "stop" in command:
            return stop_tool()
            
        elif "assess" in command or "check" in command:
            return assess_environment_tool()
            
        else:
            return f"Navigation command not recognized: {command}. Available commands: rotate clockwise/counter-clockwise [degrees], move forward [distance], move backward [distance], stop, assess environment"
            
    except Exception as e:
        return f"Error executing navigation command '{command}': {str(e)}"

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
                "3. Check current direction for potential exits",
                "4. If no exit found, turn in place and check new direction",
                "5. Continue turning and checking until exit candidate found",
                "6. Upload photos for visual confirmation of exit",
                "7. Move forward toward confirmed exit",
                "8. Reassess environment after movement",
                "9. Repeat process if path becomes blocked"
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
        elif "360" in step.lower() or "scan" in step.lower():
            # Perform 360 degree scan by rotating robot
            result = scan_360_tool(1)
            task_history.append(f"Step {step_number}: {result}")
            return f"Executed step {step_number}: {step}\nResult: {result}"
        elif "find" in step.lower() and "exit" in step.lower():
            result = find_exit_and_navigate_tool()
            task_history.append(f"Step {step_number}: {result}")
            return f"Executed step {step_number}: {step}\nResult: {result}"
        elif "rotate" in step.lower() or "face" in step.lower():
            result = "Ready to rotate to face exit direction"
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
        - Movement: drive_forward, drive_backward, stop, move_backward_safe
        - Turning: turn_in_place_right, turn_in_place_left (safe in-place rotation)
        - Servos: set_dir_servo (steering), set_cam_pan_servo, set_cam_tilt_servo, get_servo_angles
        - Sensors: get_ultrasound (distance), get_grayscale (line following)
        - Camera: init_camera, capture_image, assess_environment
        - Navigation: check_current_direction (photo + ultrasound assessment)
        - Audio: play_sound
        - Planning: create_plan, execute_plan_step
        
        CRITICAL SAFETY RULES:
        1. NEVER use turn_left or turn_right - they move forward and can hit obstacles
        2. Use turn_in_place_right_tool or turn_in_place_left_tool for all turning - they're safe
        3. Use check_current_direction_tool to assess each direction (photo + ultrasound)
        4. After every movement, use assess_environment_tool to take a photo and check sensors
        5. If distance sensor shows < 15cm, move backward using move_backward_safe_tool
        
        For escape room tasks:
        1. Initialize camera system
        2. Assess current environment
        3. If too close to obstacles, move backward to safe distance
        4. Use check_current_direction_tool to assess current direction
        5. If current direction shows an exit candidate, upload photo for visual confirmation
        6. If no exit found, use turn_in_place_right_tool or turn_in_place_left_tool to turn
        7. Repeat checking directions until an exit is found
        8. Move forward only when facing a confirmed clear direction
        
        Simple exit finding process:
        - Check current direction (photo + ultrasound)
        - If blocked or no exit, turn in place (45° increments)
        - Check new direction
        - Repeat until exit candidate found
        - Upload photos for human visual analysis and confirmation
        
        AUTOMATIC IMAGE ANALYSIS WORKFLOW:
        - When taking photos, images are automatically uploaded with contextual information
        - Context includes current sensor readings, robot status, and specific questions
        - Advanced agent analyzes uploaded images and provides navigation guidance
        - Use receive_navigation_guidance_tool to execute recommended actions
        - This creates a seamless loop: capture → upload → analyze → execute → repeat
        - Images are uploaded with specific context about what guidance is needed
        
        Always prioritize safety - use in-place rotation instead of forward-turning movements.""",
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
            turn_in_place_right_tool,
            turn_in_place_left_tool,
            check_current_direction_tool,
            upload_image_with_context,
            receive_navigation_guidance_tool,
            move_backward_safe_tool,
            assess_environment_tool,
            analyze_image_tool,
            prepare_analysis_report_tool,
            execute_navigation_command_tool,
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
    print("Commands:")
    print("  'quit' - Exit")
    print("  'reset' - Reset the robot")
    print("  'status' - Check task status")
    print("  'memory' - Test memory functionality")
    print("  'check' - Check current direction for exits")
    print("  'turn right' - Turn right in place")
    print("  'turn left' - Turn left in place")
    print("  'report' - Generate analysis report for current images")
    print("  'execute: [command]' - Execute navigation command from analysis")
    print("  'escape room' - Complex task example")
    print("Memory enabled - I will remember our conversations!")
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
            elif user_input.lower() == 'check':
                result = Runner.run_sync(agent, "Check the current direction for potential exits", session=session)
                print(f"Agent: {result.final_output}")
                continue
            elif user_input.lower() == 'turn right':
                result = Runner.run_sync(agent, "Turn right in place 45 degrees", session=session)
                print(f"Agent: {result.final_output}")
                continue
            elif user_input.lower() == 'turn left':
                result = Runner.run_sync(agent, "Turn left in place 45 degrees", session=session)
                print(f"Agent: {result.final_output}")
                continue
            elif user_input.lower() == 'report':
                result = Runner.run_sync(agent, "Prepare an analysis report for the current images and sensor data", session=session)
                print(f"Agent: {result.final_output}")
                continue
            elif user_input.lower().startswith('execute:'):
                command = user_input[8:].strip()  # Remove 'execute:' prefix
                result = Runner.run_sync(agent, f"Execute this navigation command: {command}", session=session)
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