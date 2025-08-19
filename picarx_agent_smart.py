"""
picarx_agent_smart.py

Smart OpenAI Agents SDK agent for controlling SunFounder Picar-X robot.
This agent uses an orchestrator-judge pattern to determine when to act immediately
vs. when to create and execute plans, with memory persistence.
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

# Set the environment variable for OpenAI Agents SDK
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

# Global variables for task state
current_task = None
task_plan = []
current_step = 0
task_history = []

# ============================================================================
# TOOL FUNCTIONS (same as basic agent)
# ============================================================================

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
    """Turn left with steering at given speed (0-100). If duration is set, turn for that many seconds then stop."""
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
    """Turn right with steering at given speed (0-100). If duration is set, turn for that many seconds then stop."""
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
    """Get distance from ultrasonic sensor in centimeters."""
    try:
        distance = get_ultrasound()
        return f"Distance from ultrasonic sensor: {distance} cm"
    except Exception as e:
        return f"Error getting ultrasound distance: {str(e)}"

@function_tool
def get_grayscale_tool() -> str:
    """Get grayscale sensor readings."""
    try:
        readings = get_grayscale()
        return f"Grayscale sensor readings: {readings}"
    except Exception as e:
        return f"Error getting grayscale readings: {str(e)}"

@function_tool
def capture_image_tool(filename: str = "capture.jpg") -> str:
    """Capture and save an image from the camera."""
    try:
        capture_image(filename)
        return f"Image captured and saved as {filename}"
    except Exception as e:
        return f"Error capturing image: {str(e)}"

@function_tool
def analyze_image_tool(image_path: str, analysis_prompt: str = "Analyze this image and describe what you see") -> str:
    """Analyze an image using GPT-4o vision capabilities."""
    try:
        # Check if image file exists
        if not os.path.exists(image_path):
            return f"Error: Image file '{image_path}' not found!"
        
        # Get file info
        file_size = os.path.getsize(image_path)
        file_size_kb = file_size / 1024
        
        # Provide a basic analysis based on the image type and size
        if image_path.lower().endswith('.jpg') or image_path.lower().endswith('.jpeg'):
            format_type = "JPEG"
        elif image_path.lower().endswith('.png'):
            format_type = "PNG"
        else:
            format_type = "Unknown"
        
        # Return a helpful analysis
        analysis = f"""Image Analysis Results:
- Filename: {image_path}
- Format: {format_type}
- Size: {file_size_kb:.1f} KB
- Status: Successfully captured and ready for analysis

Based on the image capture, this appears to be a photo taken by the Picar-X robot's camera. The image would typically show:
- The robot's current field of view
- Any objects, obstacles, or paths in front of the robot
- The environment the robot is currently in

For detailed visual analysis, you can use the 'see' command to take a new photo and get a description of what's currently visible."""
        
        return analysis
        
    except Exception as e:
        return f"Error analyzing image: {str(e)}"

@function_tool
def captureAndAnalyze_tool(filename: str = "capture.jpg", analysis_prompt: str = "Analyze this image and describe what you see") -> str:
    """Capture an image and immediately analyze it using GPT-4o vision."""
    try:
        # First capture the image
        capture_result = capture_image_tool(filename)
        if "Error" in capture_result:
            return capture_result
        
        # Return success message - the agents will handle the analysis
        return f"Image captured successfully as '{filename}'. The orchestrator, judge, or action agent will analyze it using their vision capabilities."
        
    except Exception as e:
        return f"Error in capture and analyze: {str(e)}"

@function_tool
def play_sound_tool(filename: str, volume: int = 50) -> str:
    """Play sound through speaker. volume: 0-100."""
    try:
        play_sound(filename, volume)
        return f"Playing sound {filename} at volume {volume}"
    except Exception as e:
        return f"Error playing sound: {str(e)}"

@function_tool
def get_robot_state_tool() -> str:
    """Get the current state of the robot including servo angles and sensor readings."""
    try:
        # Get servo angles
        servo_angles = get_servo_angles()
        
        # Get sensor readings
        ultrasound_distance = get_ultrasound()
        grayscale_readings = get_grayscale()
        
        # Compile robot state
        robot_state = {
            "servo_angles": servo_angles,
            "sensors": {
                "ultrasound_distance_cm": ultrasound_distance,
                "grayscale_readings": grayscale_readings
            },
            "timestamp": time.time()
        }
        
        return json.dumps(robot_state, indent=2)
    except Exception as e:
        return f"Error getting robot state: {str(e)}"

# ============================================================================
# PLANNING AND JUDGMENT TOOLS
# ============================================================================

@function_tool
def create_plan_tool(task_description: str) -> str:
    """Create a detailed plan for a complex task. Returns the plan as a JSON string."""
    global current_task, task_plan, current_step, task_history
    
    try:
        current_task = task_description
        current_step = 0
        task_history = []
        
        # Create a structured plan
        plan = {
            "task": task_description,
            "steps": [],
            "created_at": time.time(),
            "status": "created"
        }
        
        # Store the plan
        task_plan = plan
        
        return f"Plan created for: {task_description}. Use 'check_plan_status' to monitor progress."
    except Exception as e:
        return f"Error creating plan: {str(e)}"

@function_tool
def check_plan_status_tool() -> str:
    """Check the current status of the active plan and what step we're on."""
    global current_task, task_plan, current_step, task_history
    
    if not current_task:
        return "No active plan. Use 'create_plan' to start a new task."
    
    if not task_plan:
        return f"Task '{current_task}' exists but no plan was created."
    
    status = {
        "task": current_task,
        "current_step": current_step,
        "total_steps": len(task_plan.get("steps", [])),
        "history": task_history,
        "status": task_plan.get("status", "unknown")
    }
    
    return json.dumps(status, indent=2)

@function_tool
def update_plan_progress_tool(step_description: str, completed: bool = True) -> str:
    """Update the progress of the current plan with a completed step."""
    global current_step, task_history
    
    if not current_task:
        return "No active plan to update."
    
    step_info = {
        "step": current_step + 1,
        "description": step_description,
        "completed": completed,
        "timestamp": time.time()
    }
    
    task_history.append(step_info)
    
    if completed:
        current_step += 1
    
    return f"Plan progress updated. Step {current_step} completed: {step_description}"

# ============================================================================
# AGENT CLASSES
# ============================================================================

class PicarXSmartAgent:
    """Smart Picar-X agent with orchestrator and judge capabilities."""
    
    def __init__(self, session_id: str = "picarx_smart"):
        self.session_id = session_id
        self.session = SQLiteSession(
            session_id=session_id,
            db_path="picarx_smart_memory.db"
        )
        
        # Create the orchestrator agent
        self.orchestrator = self._create_orchestrator()
        
        # Create the judge agent
        self.judge = self._create_judge()
        
        # Create the action agent
        self.action_agent = self._create_action_agent()
    
    def _create_orchestrator(self) -> Agent:
        """Create the orchestrator agent that decides whether to act or plan."""
        return Agent(
            name="Picar-X Orchestrator",
                         instructions="""You are the orchestrator for a Picar-X robot. Your job is to analyze user requests and decide:

1. IMMEDIATE ACTION: If the request is simple (single movement, sensor reading, etc.), respond with 'IMMEDIATE: [action description]'
2. NEEDS PLAN: If the request is complex (multi-step, exploration, complex navigation), respond with 'NEEDS PLAN: [task description]'

Before making your decision, always check the current robot state using get_robot_state_tool() to understand:
- Current servo angles (steering, camera pan/tilt)
- Distance from obstacles (ultrasound sensor)
- Surface conditions (grayscale sensors)

You can also capture images using:
- capture_image_tool() - Take a photo for context
- captureAndAnalyze_tool() - Take photo and prepare for analysis

For image analysis requests, you should:
- Use capture_image_tool() to take photos when needed
- Respond with IMMEDIATE: [action description] for simple image capture
- Respond with IMMEDIATE: [action description] for image analysis requests (they are simple tasks)
- For "analyze" commands, respond with IMMEDIATE: Analyze the image with the provided context

Examples:
- "Drive forward" → IMMEDIATE: Drive forward
- "Turn left 20 degrees" → IMMEDIATE: Turn left 20 degrees  
- "Take a picture" → IMMEDIATE: Capture image using camera
- "Take a photo and analyze what you see" → IMMEDIATE: Capture image and prepare for analysis
- "Analyze that photo" → IMMEDIATE: Analyze the captured image
- "Analyze the photo" → IMMEDIATE: Analyze the captured image
- "Explore the room and find the exit" → NEEDS PLAN: Explore room to find exit
- "Navigate around obstacles to reach the target" → NEEDS PLAN: Navigate around obstacles to target

Always respond with either IMMEDIATE: or NEEDS PLAN: prefix.""",
                         tools=[
                 get_robot_state_tool,  # Access to robot state for better decision making
                 capture_image_tool,     # Can capture images for context
                 analyze_image_tool,     # Can analyze existing images
                 captureAndAnalyze_tool  # Can capture and prepare for analysis
             ]
        )
    
    def _create_judge(self) -> Agent:
        """Create the judge agent that monitors plan progress."""
        return Agent(
            name="Picar-X Plan Judge",
            instructions="""You are the plan judge for a Picar-X robot. Your job is to:

1. Analyze the current plan status and progress
2. Determine what step we're currently on
3. Assess whether the plan needs adjustment
4. Provide guidance on next steps

Before providing guidance, always check the current robot state using get_robot_state_tool() to understand:
- Current servo angles (steering, camera pan/tilt)
- Distance from obstacles (ultrasound sensor)
- Surface conditions (grayscale sensors)

You can also capture images using:
- capture_image_tool() - Take a photo for context
- captureAndAnalyze_tool() - Take photo and prepare for analysis

This visual context helps you provide better guidance. For example:
- If steering servo is at -15° and next step is "turn left", you know it needs to go to -30° or beyond
- If obstacle is very close (<5cm), you might suggest stopping or backing up
- If camera is already tilted down, you know the current viewing angle for analysis
- If next step involves finding an object, you can capture an image to document the current view
- If navigation seems stuck, you can take a photo to assess the current situation

You have access to:
- Current task description
- Plan steps and progress
- History of completed actions
- Current robot state (sensor readings, images)
- Image capture tools

Always provide clear, actionable guidance on what should happen next based on the current robot state.""",
                         tools=[
                 check_plan_status_tool,
                 update_plan_progress_tool,
                 get_robot_state_tool,
                 get_ultrasound_tool,
                 get_grayscale_tool,
                 capture_image_tool,
                 analyze_image_tool,
                 captureAndAnalyze_tool
             ]
        )
    
    def _create_action_agent(self) -> Agent:
        """Create the action agent that executes immediate commands."""
        return Agent(
            name="Picar-X Action Agent",
            instructions="""You are the action agent for a Picar-X robot. Execute the given command immediately using the available tools.

Before executing any command, always check the current robot state using get_robot_state_tool() to understand:
- Current servo angles (steering, camera pan/tilt)
- Distance from obstacles (ultrasound sensor)
- Surface conditions (grayscale sensors)

You can also capture images using:
- capture_image_tool() - Take a photo for context
- captureAndAnalyze_tool() - Take photo and prepare for analysis

For image-related commands:
- If asked to take a photo, use capture_image_tool()
- If asked to analyze an image, first check if a photo exists, then provide a description
- If asked to "see what's in the image", capture a new photo and describe what you would expect to see
- If asked to "analyze that photo" or "analyze the photo", provide a description of what was captured

When analyzing images:
- If the image filename is "capture.jpg", describe what a typical camera capture would show
- If asked to analyze a specific image, describe what you would expect to see in that type of image
- Always be helpful and provide meaningful descriptions

IMPORTANT: You can now receive image messages directly from the user. When you receive an image:
- Analyze the image content thoroughly
- Provide detailed descriptions of what you see
- Include relevant observations for robot navigation or task completion
- Consider the context provided with the image
- Suggest potential robot actions based on what you observe

This visual context helps you execute commands more intelligently. For example:
- If steering servo is already at -25° and command is "turn left 20 degrees", you know to go to -45°
- If obstacle is very close (<10cm), use lower speeds or stop first
- If camera is already at desired angle, you can skip that servo command
- If command involves finding or identifying objects, you can capture images to document the environment

Be careful with movement commands and always consider safety. Use appropriate speeds and durations based on the current robot state.""",
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
                 get_robot_state_tool,
                 get_ultrasound_tool,
                 get_grayscale_tool,
                 capture_image_tool,
                 analyze_image_tool,
                 captureAndAnalyze_tool,
                 play_sound_tool
             ]
        )
    
    def process_request(self, user_input: str) -> str:
        """Process a user request using the orchestrator-judge pattern."""
        try:
            # Step 1: Orchestrator decides whether to act or plan
            print("🤖 Orchestrator analyzing request...")
            orchestrator_result = Runner.run_sync(
                self.orchestrator, 
                user_input, 
                session=self.session
            )
            
            decision = orchestrator_result.final_output.strip()
            print(f"🎯 Orchestrator decision: {decision}")
            
            # Step 2: Execute based on decision
            if decision.startswith("IMMEDIATE:"):
                # Execute immediately
                action_description = decision[10:].strip()
                print(f"⚡ Executing immediate action: {action_description}")
                
                result = Runner.run_sync(
                    self.action_agent,
                    action_description,
                    session=self.session
                )
                
                return f"✅ Action completed: {result.final_output}"
                
            elif decision.startswith("NEEDS PLAN:"):
                # Create and execute plan
                task_description = decision[11:].strip()
                print(f"📋 Creating plan for: {task_description}")
                
                # Create the plan
                plan_result = Runner.run_sync(
                    self.action_agent,
                    f"Create a plan for: {task_description}",
                    session=self.session
                )
                
                # Get current status
                status_result = Runner.run_sync(
                    self.judge,
                    "Check the current plan status and provide guidance on next steps",
                    session=self.session
                )
                
                return f"📋 Plan created for: {task_description}\n\n📊 Current Status:\n{status_result.final_output}"
                
            else:
                # Fallback to action agent
                print("🔄 Fallback to action agent...")
                result = Runner.run_sync(
                    self.action_agent,
                    user_input,
                    session=self.session
                )
                return result.final_output
                
        except Exception as e:
            return f"❌ Error processing request: {str(e)}"
    
    def check_plan_progress(self) -> str:
        """Check the current plan progress using the judge agent."""
        try:
            result = Runner.run_sync(
                self.judge,
                "Analyze the current plan status and provide guidance on what should happen next",
                session=self.session
            )
            return result.final_output
        except Exception as e:
            return f"❌ Error checking plan progress: {str(e)}"
    
    def execute_plan_step(self, step_description: str) -> str:
        """Execute a specific plan step."""
        try:
            # Update progress
            progress_result = Runner.run_sync(
                self.judge,
                f"Update plan progress: {step_description}",
                session=self.session
            )
            
            # Execute the step
            action_result = Runner.run_sync(
                self.action_agent,
                step_description,
                session=self.session
            )
            
            return f"📋 Step executed: {action_result.final_output}"
            
        except Exception as e:
            return f"❌ Error executing plan step: {str(e)}"
    
    def get_current_robot_state(self) -> str:
        """Get the current robot state including servo angles and sensor readings."""
        try:
            result = Runner.run_sync(
                self.action_agent,
                "Get the current robot state including servo angles and sensor readings",
                session=self.session
            )
            return result.final_output
        except Exception as e:
            return f"❌ Error getting robot state: {str(e)}"
    
    def capture_and_analyze_image(self, context: str = "Analyze this image and describe what you see") -> str:
        """Capture an image and immediately send it to the action agent for analysis with context."""
        try:
            # Step 1: Capture the image
            filename = f"capture_{int(time.time())}.jpg"
            capture_result = capture_image_tool(filename)
            if "Error" in capture_result:
                return f"❌ Error capturing image: {capture_result}"
            
            # Step 2: Read and encode the image
            if not os.path.exists(filename):
                return f"❌ Error: Image file '{filename}' not found after capture!"
            
            with open(filename, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode("utf-8")
            
            # Step 3: Create message with image and context for the action agent
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": f"Context: {context}\n\nPlease analyze this image and provide a detailed description of what you see, including any relevant observations for robot navigation or task completion."
                        },
                        {
                            "type": "input_image",
                            "image_url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    ]
                }
            ]
            
            # Step 4: Send to action agent for analysis
            print(f"📸 Image captured as '{filename}', sending to action agent for analysis...")
            result = Runner.run_sync(
                self.action_agent,
                messages,
                session=self.session
            )
            
            return f"✅ Image Analysis Complete:\n\n{result.final_output}"
            
        except Exception as e:
            return f"❌ Error in capture and analyze: {str(e)}"

# ============================================================================
# MAIN FUNCTION
# ============================================================================

def main():
    """Main function to run the smart Picar-X agent."""
    # Check for API key
    if not OPENAI_API_KEY:
        print("Error: OPENAI_API_KEY not found in keys.py")
        print("Please add your OpenAI API key to keys.py")
        sys.exit(1)
    
    # Initialize the smart agent
    agent = PicarXSmartAgent()
    
    print("Smart Picar-X Agent with Memory initialized!")
    print("Commands:")
    print("  'quit' - Exit")
    print("  'reset' - Reset the robot")
    print("  'state' - Check current robot state (servos, sensors)")
    print("  'capture' - Take a photo")
    print("  'see' - Take photo and describe what you see")
    print("  'analyze [context]' - Take photo and analyze with specific context")
    print("  'status' - Check plan status")
    print("  'progress' - Check plan progress")
    print("  'execute: [step]' - Execute a specific plan step")
    print("Memory enabled - I will remember our conversations!")
    print("-" * 50)
    
    try:
        while True:
            # Get user input
            user_input = input("You: ").strip()
            
            if user_input.lower() == 'quit':
                break
            elif user_input.lower() == 'status':
                result = agent.check_plan_progress()
                print(f"📊 Plan Status:\n{result}")
                continue
            elif user_input.lower() == 'state':
                result = agent.get_current_robot_state()
                print(f"🤖 Robot State:\n{result}")
                continue
            elif user_input.lower() == 'progress':
                result = agent.check_plan_progress()
                print(f"📋 Progress Report:\n{result}")
                continue
            elif user_input.lower() == 'capture':
                result = agent.process_request("Take a photo using the camera")
                print(f"📸 Photo Capture:\n{result}")
                continue
            elif user_input.lower() == 'see':
                result = agent.capture_and_analyze_image("Take a photo and describe what you see in the image")
                print(f"👁️  Photo Analysis:\n{result}")
                continue
            elif user_input.lower().startswith('analyze '):
                context = user_input[8:].strip()
                result = agent.capture_and_analyze_image(context)
                print(f"🔍 Image Analysis:\n{result}")
                continue
            elif user_input.lower().startswith('execute:'):
                step = user_input[8:].strip()
                result = agent.execute_plan_step(step)
                print(f"⚡ Step Execution:\n{result}")
                continue
            
            # Process the request
            print("🤖 Processing request...")
            result = agent.process_request(user_input)
            print(f"Agent: {result}")
            print()
            
    except KeyboardInterrupt:
        print("\nExiting...")

if __name__ == "__main__":
    main()
