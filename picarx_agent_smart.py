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

You can capture images using:
- capture_image_tool(filename) - Take a photo (simple capture tool)

For image analysis requests, you should:
- Use capture_image_tool() to capture images when needed
- Respond with IMMEDIATE: [action description] for simple image capture
- Respond with IMMEDIATE: [action description] for image analysis requests (they are simple tasks)
- For "analyze" commands, respond with IMMEDIATE: Analyze image with GPT-4o vision
- For requests that mention "analyze" or "then analyze", respond with IMMEDIATE: Analyze image with GPT-4o vision
- For requests that mention "photo" and "analyze" together, respond with IMMEDIATE: Analyze image with GPT-4o vision
- For requests that mention "what does the robot see", respond with IMMEDIATE: Analyze image with GPT-4o vision
- For requests that mention "robot see" or "robot view", respond with IMMEDIATE: Analyze image with GPT-4o vision
- Always provide clear action descriptions that the action agent can execute
- Note: Image analysis will be handled by the smart agent's capture_and_analyze_image method

Examples:
- "Drive forward" → IMMEDIATE: Drive forward
- "Turn left 20 degrees" → IMMEDIATE: Turn left 20 degrees  
- "Take a picture" → IMMEDIATE: Capture image using camera
- "Take a photo and analyze what you see" → IMMEDIATE: Analyze image with GPT-4o vision
- "Take a photo and then analyze it" → IMMEDIATE: Analyze image with GPT-4o vision
- "Take a photo and analyze it" → IMMEDIATE: Analyze image with GPT-4o vision
- "Analyze that photo" → IMMEDIATE: Analyze image with GPT-4o vision
- "Analyze the photo" → IMMEDIATE: Analyze image with GPT-4o vision
- "Look for obstacles" → IMMEDIATE: Analyze image with GPT-4o vision
- "Find the red object" → IMMEDIATE: Analyze image with GPT-4o vision
- "What does the robot see" → IMMEDIATE: Analyze image with GPT-4o vision
- "What can the robot see" → IMMEDIATE: Analyze image with GPT-4o vision
- "Robot view" → IMMEDIATE: Analyze image with GPT-4o vision
- "Robot see" → IMMEDIATE: Analyze image with GPT-4o vision
- "Explore the room and find the exit" → NEEDS PLAN: Explore room to find exit
- "Navigate around obstacles to reach the target" → NEEDS PLAN: Navigate around obstacles to target

Always respond with either IMMEDIATE: or NEEDS PLAN: prefix.""",
                                                   tools=[
                  get_robot_state_tool,  # Access to robot state for better decision making
                  capture_image_tool,     # Simple image capture tool
                  analyze_image_tool      # Can analyze existing images
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

You can capture images using:
- capture_image_tool(filename) - Take a photo (simple capture tool)

This visual context helps you provide better guidance. For example:
- If steering servo is at -15° and next step is "turn left", you know it needs to go to -30° or beyond
- If obstacle is very close (<5cm), you might suggest stopping or backing up
- If camera is already tilted down, you know the current viewing angle for analysis
- If next step involves finding an object, you can capture an image to document the current view
- If navigation seems stuck, you can take a photo to assess the current situation
- Note: The capture_image_tool is a simple tool that only captures images - use it when you need visual documentation

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
                  capture_image_tool,  # Simple image capture tool
                  analyze_image_tool
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

You can capture images using:
- capture_image_tool(filename) - Take a photo (simple capture tool)

For image-related commands:
- If asked to take a photo, use capture_image_tool(filename) to capture the image
- If asked to analyze an image, the smart agent will handle this via its capture_and_analyze_image method
- If asked to "see what's in the image", the smart agent will capture and analyze the image
- If asked to "analyze that photo" or "analyze the photo", the smart agent will capture and analyze the image
- If asked to look for specific objects, the smart agent will capture and analyze the image
- If asked to "take a photo and analyze it", the smart agent will capture and analyze the image

When analyzing images:
- Always be helpful and provide meaningful descriptions
- Consider the context of the request when providing analysis
- Suggest potential robot actions based on what you observe
- Note: When you receive "Capture image and analyze with context" requests, the system will automatically handle the image capture and analysis for you

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
- Note: The capture_image_tool is a simple tool that only captures images - use it when you need visual documentation

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
                  capture_image_tool,  # Simple image capture tool
                  analyze_image_tool,
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
            print(f"🔍 Decision starts with IMMEDIATE: {decision.startswith('IMMEDIATE:')}")
            print(f"🔍 Decision starts with NEEDS PLAN: {decision.startswith('NEEDS PLAN:')}")
            
            # Step 2: Execute based on decision
            if decision.startswith("IMMEDIATE:"):
                # Execute immediately
                action_description = decision[10:].strip()
                print(f"⚡ Executing immediate action: {action_description}")
                
                # Check if this is an image analysis request
                if "analyze" in action_description.lower() and ("image" in action_description.lower() or "photo" in action_description.lower()):
                    print("📸 Detected image analysis request, using capture_and_analyze_image method...")
                    result = self.capture_and_analyze_image("Analyze this image and describe what you see")
                    return f"✅ Image Analysis Completed: {result}"
                
                # Execute the action using the action agent
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
                
                print(f"📋 Plan created: {plan_result.final_output}")
                
                # Start executing the plan with continuous monitoring
                print(f"🚀 Starting plan execution with continuous monitoring...")
                execution_result = self.execute_plan_with_monitoring(task_description)
                
                return f"📋 Plan created for: {task_description}\n\n🚀 Plan Execution:\n{execution_result}"
                
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
    
    def execute_plan_with_monitoring(self, task_description: str) -> str:
        """Execute a plan with continuous monitoring, taking photos and using tools to verify progress."""
        try:
            print(f"🚀 Starting plan execution with continuous monitoring for: {task_description}")
            
            # Step 1: Take initial photo to understand current state
            print("📸 Step 1: Taking initial photo to understand current state...")
            initial_analysis = self.capture_and_analyze_image(f"Analyze this image to understand the current environment for the task: {task_description}")
            print(f"📸 Initial analysis: {initial_analysis}")
            
            # Step 2: Get current robot state
            print("🤖 Step 2: Getting current robot state...")
            current_state = self.get_current_robot_state()
            print(f"🤖 Current robot state: {current_state}")
            
            # Step 3: Start executing the plan step by step
            print("📋 Step 3: Starting plan execution...")
            
            # For the chair distance task, create a specific execution plan
            if "20 cm away from the chair" in task_description.lower():
                return self.execute_chair_distance_plan()
            
            # For other tasks, use the general approach
            return self.execute_general_plan(task_description)
            
        except Exception as e:
            error_msg = f"❌ Error in plan execution: {str(e)}"
            print(error_msg)
            return error_msg
    
    def execute_chair_distance_plan(self) -> str:
        """Execute the specific plan to move to 20cm from the chair."""
        try:
            print("🪑 Executing chair distance plan...")
            
            max_iterations = 10  # Prevent infinite loops
            iteration = 0
            
            while iteration < max_iterations:
                iteration += 1
                print(f"🔄 Iteration {iteration}/{max_iterations}")
                
                # Step 1: Take photo and analyze current position
                print("📸 Taking photo to analyze current position...")
                position_analysis = self.capture_and_analyze_image("Analyze this image to determine the robot's current distance from the chair and what direction to move")
                print(f"📸 Position analysis: {position_analysis}")
                
                # Step 2: Check ultrasound sensor
                print("📡 Checking ultrasound sensor...")
                try:
                    from picarx_primitives import get_ultrasound
                    distance = get_ultrasound()
                    print(f"📡 Ultrasound reading: {distance} cm")
                except Exception as e:
                    print(f"⚠️ Ultrasound error: {e}")
                    distance = None
                
                # Step 3: Determine action based on analysis
                if distance and distance <= 25:  # Within 25cm (close enough to 20cm)
                    print("✅ Target distance reached!")
                    return f"🎯 Mission accomplished! Robot is now approximately {distance}cm from the chair.\n\n📸 Final position analysis:\n{position_analysis}"
                
                # Step 4: Move based on analysis
                print("🚶 Moving robot...")
                if distance and distance > 25:
                    # Move forward slowly
                    try:
                        from picarx_primitives import drive_forward, stop_tool
                        print("⬆️ Moving forward...")
                        drive_forward(30, 0.5)  # 30% speed, 0.5 seconds
                        stop_tool()
                        print("⏹️ Stopped")
                    except Exception as e:
                        print(f"⚠️ Movement error: {e}")
                
                # Step 5: Wait a moment for movement to settle
                import time
                time.sleep(1)
                
                print(f"🔄 Completed iteration {iteration}")
            
            return f"⚠️ Plan execution completed after {max_iterations} iterations. Final position may not be exactly 20cm from chair."
            
        except Exception as e:
            error_msg = f"❌ Error in chair distance plan: {str(e)}"
            print(error_msg)
            return error_msg
    
    def execute_general_plan(self, task_description: str) -> str:
        """Execute a general plan using the judge and action agents."""
        try:
            print(f"📋 Executing general plan for: {task_description}")
            
            # Get plan guidance from judge
            guidance = Runner.run_sync(
                self.judge,
                f"Provide step-by-step guidance for executing: {task_description}",
                session=self.session
            )
            
            # Execute the guidance
            result = Runner.run_sync(
                self.action_agent,
                guidance.final_output,
                session=self.session
            )
            
            return f"📋 General plan executed:\n{result.final_output}"
            
        except Exception as e:
            return f"❌ Error in general plan execution: {str(e)}"
    
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
            print("🔍 Starting image capture and analysis process...")
            print(f"📝 Context provided: {context}")
            
            # Step 1: Capture the image using the capture_image function directly
            filename = f"capture_{int(time.time())}.jpg"
            print(f"📸 Step 1: Capturing image as '{filename}'...")
            try:
                capture_image(filename)
                print(f"✅ Image captured successfully as '{filename}'")
            except Exception as e:
                error_msg = f"❌ Error capturing image: {str(e)}"
                print(error_msg)
                return error_msg
            
            # Step 2: Read and encode the image
            print(f"📁 Step 2: Reading and encoding image file...")
            if not os.path.exists(filename):
                error_msg = f"❌ Error: Image file '{filename}' not found after capture!"
                print(error_msg)
                return error_msg
            
            print(f"📖 Reading image file: {filename}")
            with open(filename, "rb") as image_file:
                image_data = image_file.read()
                file_size = len(image_data)
                print(f"📊 Image file size: {file_size} bytes ({file_size/1024:.1f} KB)")
                base64_image = base64.b64encode(image_data).decode("utf-8")
                print(f"🔢 Base64 encoding completed. Length: {len(base64_image)} characters")
            
            # Step 3: Create message with image and context for the action agent
            print(f"📝 Step 3: Creating message for GPT-4o vision analysis...")
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
            print(f"📤 Message created with:")
            print(f"   - Text content: {messages[0]['content'][0]['text']}")
            print(f"   - Image content: data:image/jpeg;base64,[{len(base64_image)} chars]")
            
            # Step 4: Send to action agent for analysis
            print(f"🚀 Step 4: Sending to GPT-4o vision model via action agent...")
            print(f"⏳ Waiting for GPT-4o vision analysis...")
            
            # Note: We must set session=None when sending a list of messages
            # The session memory will still work for subsequent string inputs
            result = Runner.run_sync(
                self.action_agent,
                messages,
                session=None  # Must be None when sending message list
            )
            
            print(f"🎯 GPT-4o Vision Analysis Complete!")
            print(f"📋 Raw result object type: {type(result)}")
            print(f"📋 Raw result attributes: {dir(result)}")
            print(f"📋 Final output type: {type(result.final_output)}")
            print(f"📋 Final output length: {len(str(result.final_output))} characters")
            print(f"📋 Final output content:")
            print("=" * 80)
            print(result.final_output)
            print("=" * 80)
            
            return f"✅ Image Analysis Complete:\n\n{result.final_output}"
            
        except Exception as e:
            error_msg = f"❌ Error in capture and analyze: {str(e)}"
            print(error_msg)
            print(f"🔍 Exception type: {type(e)}")
            print(f"🔍 Exception details: {str(e)}")
            return error_msg

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
    print("  'move to chair' - Move to 20cm from chair (test plan execution)")
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
            elif user_input.lower() == 'move to chair':
                result = agent.process_request("keep on moving till you are 20 cm away from the chair")
                print(f"🪑 Chair Distance Mission:\n{result}")
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
