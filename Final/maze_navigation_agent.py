"""
Maze Navigation Agent for Picar-X Robot

This agent understands robot movement calibration and uses bird's-eye view analysis
to navigate through mazes with black line boundaries. It includes multithreaded
grayscale monitoring for safety and memory-based navigation tracking.
"""

import os
import sys
import time
import threading
import base64
import json
from typing import List, Optional, Dict, Any, Tuple
from agents import Agent, Runner
from agents import function_tool
from agents.memory import SQLiteSession
from PIL import Image
import io

# Import the primitives and keys
from final_primitives import *
from keys import OPENAI_API_KEY

# Set the environment variable for OpenAI Agents SDK
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

# Global variables for navigation state
navigation_state = {
    'current_position': {'x': 0, 'y': 0, 'heading': 0},  # Relative position tracking
    'last_action': None,
    'boundary_hit': False,
    'maze_layout': None,
    'target_position': None,
    'path_history': [],
    'grayscale_monitoring': False
}

# Threading control
grayscale_thread = None
stop_grayscale_monitoring = threading.Event()

class MazeNavigationAgent:
    """Smart maze navigation agent with calibration knowledge and safety monitoring."""
    
    def __init__(self, session_id: str = "maze_navigation"):
        self.session_id = session_id
        self.session = SQLiteSession(
            session_id=session_id,
            db_path="maze_navigation_memory.db"
        )
        
        # Create the navigation agent
        self.navigation_agent = self._create_navigation_agent()
        
        # Movement calibration constants
        self.calibration = {
            'forward_speed_30_duration_1': 30,  # 30cm in 1 second at speed 30
            'turn_speed_50_duration_2_1': 90,   # 90 degrees in 2.1 seconds at speed 50
            'cm_per_second_at_speed_30': 30,
            'degrees_per_second_at_speed_50': 42.86  # 90/2.1
        }
    
    def _create_navigation_agent(self) -> Agent:
        """Create the navigation agent with maze understanding capabilities."""
        return Agent(
            name="Maze Navigation Agent",
            instructions="""You are a specialized maze navigation agent for a Picar-X robot. You understand:

MOVEMENT CALIBRATION:
- Speed 30 for 1 second = 30 centimeters forward
- Speed 50 for 2.1 seconds = 90 degrees turn
- Speed 20 for 0.5 seconds = 15 centimeters forward
- Speed 40 for 1.4 seconds = 60 degrees turn

MAZE ANALYSIS:
- Analyze bird's-eye view images to understand maze layout
- Identify black line boundaries and pathways
- Plan optimal routes through the maze
- Track robot position relative to maze structure

SAFETY MONITORING:
- The robot has multithreaded grayscale monitoring
- If a black line is detected (boundary hit), the robot will stop
- You will be notified of the last action that caused the boundary hit
- Always consider safety when planning movements

NAVIGATION STRATEGY:
1. Take bird's-eye view photo to understand maze layout
2. Identify current position and target destination
3. Plan a path avoiding black line boundaries
4. Execute movements with appropriate calibration
5. Monitor for boundary hits and adjust strategy
6. Use memory to track successful paths and avoid dead ends

When you receive a maze navigation request:
1. First capture a bird's-eye view image
2. Analyze the maze layout and identify pathways
3. Plan a safe route to the target
4. Execute the navigation step by step
5. Monitor for boundary hits and adjust as needed

Always be cautious with movements near boundaries and use smaller, safer movements when close to black lines.""",
            tools=[
                reset_tool,
                move_forward_tool,
                move_backward_tool,
                turn_left_tool,
                turn_right_tool,
                set_dir_servo_tool,
                get_robot_state_tool,
                get_grayscale_tool,
                capture_birdseye_image_tool,
                plan_navigation_path_tool,
                check_boundary_status_tool,
                update_position_tool,
                get_navigation_status_tool
            ]
        )
    
    def start_grayscale_monitoring(self):
        """Start multithreaded grayscale monitoring for boundary detection."""
        global grayscale_thread, stop_grayscale_monitoring, navigation_state
        
        if grayscale_thread and grayscale_thread.is_alive():
            return  # Already monitoring
        
        stop_grayscale_monitoring.clear()
        navigation_state['grayscale_monitoring'] = True
        
        def monitor_grayscale():
            """Monitor grayscale sensors for black line detection."""
            while not stop_grayscale_monitoring.is_set():
                try:
                    grayscale_values = get_grayscale()
                    
                    # Check for black line detection (values below threshold)
                    black_line_threshold = 1000  # Adjust based on your surface
                    if any(value < black_line_threshold for value in grayscale_values):
                        print("🚨 BLACK LINE DETECTED - BOUNDARY HIT!")
                        navigation_state['boundary_hit'] = True
                        # Emergency stop - call the stop function from primitives
                        try:
                            from final_primitives import stop
                            stop()
                        except:
                            pass  # If stop function not available, continue
                        
                        # Log the boundary hit with last action
                        boundary_log = {
                            'timestamp': time.time(),
                            'last_action': navigation_state['last_action'],
                            'grayscale_values': grayscale_values,
                            'position': navigation_state['current_position'].copy()
                        }
                        
                        print(f"🚨 Boundary hit details: {boundary_log}")
                        
                        # Store in memory
                        self._log_boundary_hit(boundary_log)
                        
                        # Wait a bit before continuing monitoring
                        time.sleep(2)
                    
                    time.sleep(0.1)  # Check every 100ms
                    
                except Exception as e:
                    print(f"⚠️ Grayscale monitoring error: {e}")
                    time.sleep(0.5)
        
        grayscale_thread = threading.Thread(target=monitor_grayscale, daemon=True)
        grayscale_thread.start()
        print("🔍 Grayscale monitoring started")
    
    def stop_grayscale_monitoring(self):
        """Stop grayscale monitoring."""
        global stop_grayscale_monitoring, navigation_state
        stop_grayscale_monitoring.set()
        navigation_state['grayscale_monitoring'] = False
        print("🔍 Grayscale monitoring stopped")
    
    def _log_boundary_hit(self, boundary_log: dict):
        """Log boundary hit to memory."""
        try:
            # Store in session memory
            result = Runner.run_sync(
                self.navigation_agent,
                f"Log boundary hit: {json.dumps(boundary_log)}",
                session=self.session
            )
        except Exception as e:
            print(f"⚠️ Error logging boundary hit: {e}")
    
    def navigate_maze(self, target_description: str = "navigate to the end of the maze") -> str:
        """Main maze navigation function with command list execution."""
        try:
            print(f"🎯 Starting maze navigation: {target_description}")
            
            # Reset robot state
            reset()
            navigation_state['current_position'] = {'x': 0, 'y': 0, 'heading': 0}
            navigation_state['boundary_hit'] = False
            navigation_state['path_history'] = []
            
            # Step 1: Get command list from agent
            print("📋 Step 1: Getting navigation command list from agent...")
            command_list = self.get_navigation_commands(target_description)
            
            if not command_list:
                return "❌ Failed to get navigation commands from agent"
            
            print(f"📋 Received {len(command_list)} commands to execute")
            
            # Step 2: Execute commands with monitoring
            print("🚀 Step 2: Executing commands with grayscale monitoring...")
            execution_result = self.execute_command_list(command_list)
            
            return f"🎯 Maze Navigation Complete:\n{execution_result}"
            
        except Exception as e:
            return f"❌ Navigation error: {str(e)}"
    
    def get_navigation_commands(self, target_description: str) -> List[Dict]:
        """Get a list of navigation commands from the agent based on bird's-eye view."""
        try:
            # First, capture bird's-eye view
            print("📸 Capturing bird's-eye view...")
            capture_birdseye_image_tool("maze_analysis.jpg")
            
            # Get commands from agent
            result = Runner.run_sync(
                self.navigation_agent,
                f"""Analyze the maze image 'maze_analysis.jpg' and create a detailed command list to navigate: {target_description}

Return ONLY a JSON list of commands in this exact format:
[
    {{"action": "move_forward", "speed": 30, "duration": 1.0, "description": "Move forward 30cm"}},
    {{"action": "turn_right", "speed": 50, "duration": 2.1, "description": "Turn right 90 degrees"}},
    {{"action": "move_forward", "speed": 20, "duration": 0.5, "description": "Move forward 15cm"}},
    {{"action": "turn_left", "speed": 50, "duration": 1.4, "description": "Turn left 60 degrees"}}
]

Use these movement calibrations:
- Speed 30 for 1 second = 30 centimeters forward
- Speed 50 for 2.1 seconds = 90 degrees turn
- Speed 20 for 0.5 seconds = 15 centimeters forward
- Speed 40 for 1.4 seconds = 60 degrees turn

Plan a safe path avoiding black line boundaries. Return ONLY the JSON array, no other text.""",
                session=self.session
            )
            
            # Parse the JSON response
            import json
            commands = json.loads(result.final_output.strip())
            return commands
            
        except Exception as e:
            print(f"❌ Error getting navigation commands: {e}")
            return []
    
    def execute_command_list(self, commands: List[Dict]) -> str:
        """Execute a list of commands with grayscale monitoring."""
        try:
            execution_log = []
            successful_commands = 0
            
            for i, command in enumerate(commands):
                print(f"\n🔄 Executing command {i+1}/{len(commands)}: {command}")
                
                # Reset boundary hit flag
                navigation_state['boundary_hit'] = False
                
                # Start monitoring for this command
                self.start_grayscale_monitoring()
                
                try:
                    # Execute the command
                    result = self.execute_single_command(command)
                    execution_log.append({
                        'command_index': i,
                        'command': command,
                        'result': result,
                        'success': True,
                        'boundary_hit': False
                    })
                    
                    if not navigation_state['boundary_hit']:
                        successful_commands += 1
                        print(f"✅ Command {i+1} completed successfully")
                    else:
                        print(f"🚨 Command {i+1} hit boundary - stopping execution")
                        break
                        
                except Exception as e:
                    execution_log.append({
                        'command_index': i,
                        'command': command,
                        'result': f"Error: {str(e)}",
                        'success': False,
                        'boundary_hit': navigation_state['boundary_hit']
                    })
                    print(f"❌ Command {i+1} failed: {e}")
                    break
                
                finally:
                    # Stop monitoring after each command
                    self.stop_grayscale_monitoring()
                    time.sleep(0.5)  # Brief pause between commands
            
            # If boundary was hit, get course correction
            if navigation_state['boundary_hit']:
                print("🔄 Boundary hit detected - getting course correction...")
                correction_result = self.get_course_correction(execution_log)
                return f"🚨 Navigation stopped due to boundary hit at command {len(execution_log)}.\n\nCourse Correction:\n{correction_result}\n\nExecution Log:\n{json.dumps(execution_log, indent=2)}"
            else:
                return f"✅ All {successful_commands} commands executed successfully!\n\nExecution Log:\n{json.dumps(execution_log, indent=2)}"
                
        except Exception as e:
            return f"❌ Error executing command list: {str(e)}"
    
    def execute_single_command(self, command: Dict) -> str:
        """Execute a single navigation command."""
        action = command.get('action')
        speed = command.get('speed', 30)
        duration = command.get('duration', 1.0)
        
        if action == 'move_forward':
            return move_forward_tool(speed, duration)
        elif action == 'move_backward':
            return move_backward_tool(speed, duration)
        elif action == 'turn_left':
            return turn_left_tool(speed, duration)
        elif action == 'turn_right':
            return turn_right_tool(speed, duration)
        elif action == 'set_dir_servo':
            angle = command.get('angle', 0)
            return set_dir_servo_tool(angle)
        else:
            return f"Unknown action: {action}"
    
    def get_course_correction(self, execution_log: List[Dict]) -> str:
        """Get course correction from agent after boundary hit."""
        try:
            # Find the command that hit the boundary
            failed_command = None
            for log_entry in reversed(execution_log):
                if log_entry.get('boundary_hit', False):
                    failed_command = log_entry
                    break
            
            if not failed_command:
                return "No boundary hit found in execution log"
            
            # Get current robot state
            current_state = self.get_navigation_status()
            
            # Ask agent for course correction
            correction_prompt = f"""The robot hit a boundary while executing this command:
{json.dumps(failed_command, indent=2)}

Current robot state:
{json.dumps(current_state, indent=2)}

Please provide a course correction strategy. Return ONLY a JSON list of new commands to continue navigation, or an empty list [] if the maze cannot be completed from this position.

Use the same command format as before:
[
    {{"action": "move_forward", "speed": 20, "duration": 0.5, "description": "Back up slowly"}},
    {{"action": "turn_right", "speed": 50, "duration": 1.4, "description": "Turn right 60 degrees"}}
]"""
            
            result = Runner.run_sync(
                self.navigation_agent,
                correction_prompt,
                session=self.session
            )
            
            return result.final_output
            
        except Exception as e:
            return f"❌ Error getting course correction: {str(e)}"
    
    def execute_course_correction(self, correction_commands: List[Dict]) -> str:
        """Execute course correction commands after boundary hit."""
        try:
            if not correction_commands:
                return "No course correction commands provided"
            
            print(f"🔄 Executing {len(correction_commands)} course correction commands...")
            return self.execute_command_list(correction_commands)
            
        except Exception as e:
            return f"❌ Error executing course correction: {str(e)}"
    
    def get_navigation_status(self) -> dict:
        """Get current navigation status."""
        return {
            'position': navigation_state['current_position'],
            'last_action': navigation_state['last_action'],
            'boundary_hit': navigation_state['boundary_hit'],
            'grayscale_monitoring': navigation_state['grayscale_monitoring'],
            'path_history': navigation_state['path_history']
        }

# ============================================================================
# FUNCTION TOOLS FOR MAZE NAVIGATION
# ============================================================================

@function_tool
def reset_tool() -> str:
    """Reset all servos to 0 and stop the motors."""
    try:
        reset()
        navigation_state['last_action'] = 'reset'
        return "Robot reset: all servos to 0, motors stopped"
    except Exception as e:
        return f"Error resetting robot: {str(e)}"

@function_tool
def move_forward_tool(speed: int, duration: float) -> str:
    """Move forward with calibration knowledge. Speed 30 for 1 second = 30cm."""
    try:
        move_forward(speed, duration)
        navigation_state['last_action'] = f'move_forward({speed}, {duration})'
        
        # Update position based on calibration
        distance_cm = (speed / 30) * 30 * duration  # Calibration: speed 30 = 30cm/s
        navigation_state['current_position']['x'] += distance_cm * 0.01  # Convert to meters
        navigation_state['path_history'].append({
            'action': 'forward',
            'speed': speed,
            'duration': duration,
            'distance_cm': distance_cm,
            'position': navigation_state['current_position'].copy()
        })
        
        return f"Moved forward {distance_cm:.1f}cm at speed {speed} for {duration}s"
    except Exception as e:
        return f"Error moving forward: {str(e)}"

@function_tool
def move_backward_tool(speed: int, duration: float) -> str:
    """Move backward with calibration knowledge."""
    try:
        move_backward(speed, duration)
        navigation_state['last_action'] = f'move_backward({speed}, {duration})'
        
        # Update position
        distance_cm = (speed / 30) * 30 * duration
        navigation_state['current_position']['x'] -= distance_cm * 0.01
        navigation_state['path_history'].append({
            'action': 'backward',
            'speed': speed,
            'duration': duration,
            'distance_cm': distance_cm,
            'position': navigation_state['current_position'].copy()
        })
        
        return f"Moved backward {distance_cm:.1f}cm at speed {speed} for {duration}s"
    except Exception as e:
        return f"Error moving backward: {str(e)}"

@function_tool
def turn_left_tool(speed: int, duration: float) -> str:
    """Turn left with calibration knowledge. Speed 50 for 2.1 seconds = 90 degrees."""
    try:
        turn_left(speed, duration)
        navigation_state['last_action'] = f'turn_left({speed}, {duration})'
        
        # Update heading based on calibration
        degrees_turned = (speed / 50) * 90 * (duration / 2.1)  # Calibration: speed 50 = 90°/2.1s
        navigation_state['current_position']['heading'] -= degrees_turned
        navigation_state['path_history'].append({
            'action': 'turn_left',
            'speed': speed,
            'duration': duration,
            'degrees': degrees_turned,
            'position': navigation_state['current_position'].copy()
        })
        
        return f"Turned left {degrees_turned:.1f}° at speed {speed} for {duration}s"
    except Exception as e:
        return f"Error turning left: {str(e)}"

@function_tool
def turn_right_tool(speed: int, duration: float) -> str:
    """Turn right with calibration knowledge. Speed 50 for 2.1 seconds = 90 degrees."""
    try:
        turn_right(speed, duration)
        navigation_state['last_action'] = f'turn_right({speed}, {duration})'
        
        # Update heading
        degrees_turned = (speed / 50) * 90 * (duration / 2.1)
        navigation_state['current_position']['heading'] += degrees_turned
        navigation_state['path_history'].append({
            'action': 'turn_right',
            'speed': speed,
            'duration': duration,
            'degrees': degrees_turned,
            'position': navigation_state['current_position'].copy()
        })
        
        return f"Turned right {degrees_turned:.1f}° at speed {speed} for {duration}s"
    except Exception as e:
        return f"Error turning right: {str(e)}"

@function_tool
def set_dir_servo_tool(angle: float) -> str:
    """Set steering servo angle for precise navigation."""
    try:
        set_dir_servo(angle)
        navigation_state['last_action'] = f'set_dir_servo({angle})'
        return f"Steering servo set to {angle}°"
    except Exception as e:
        return f"Error setting steering servo: {str(e)}"

@function_tool
def get_robot_state_tool() -> str:
    """Get current robot state including position and sensors."""
    try:
        servo_angles = get_servo_angles()
        ultrasound_distance = get_ultrasound()
        grayscale_readings = get_grayscale()
        
        robot_state = {
            "servo_angles": servo_angles,
            "sensors": {
                "ultrasound_distance_cm": ultrasound_distance,
                "grayscale_readings": grayscale_readings
            },
            "navigation": navigation_state,
            "timestamp": time.time()
        }
        
        return json.dumps(robot_state, indent=2)
    except Exception as e:
        return f"Error getting robot state: {str(e)}"

@function_tool
def get_grayscale_tool() -> str:
    """Get grayscale sensor readings for boundary detection."""
    try:
        readings = get_grayscale()
        return f"Grayscale readings: {readings} (values below 1000 indicate black lines)"
    except Exception as e:
        return f"Error getting grayscale readings: {str(e)}"

@function_tool
def capture_birdseye_image_tool(filename: str = "maze_birdseye.jpg") -> str:
    """Capture a bird's-eye view image of the maze for analysis."""
    try:
        # Set camera to look down for bird's-eye view
        set_cam_tilt_servo(-30)  # Tilt down
        set_cam_pan_servo(0)     # Center pan
        time.sleep(0.5)  # Let camera adjust
        
        # Capture image
        capture_image(filename)
        
        # Reset camera
        set_cam_tilt_servo(0)
        set_cam_pan_servo(0)
        
        return f"Bird's-eye view captured as {filename}"
    except Exception as e:
        return f"Error capturing bird's-eye view: {str(e)}"

def analyze_maze_layout_tool(image_path: str, navigation_agent, session) -> str:
    """Analyze maze layout from bird's-eye view image."""
    try:
        if not os.path.exists(image_path):
            return f"Error: Image file '{image_path}' not found!"
        
        # Read and encode image
        with open(image_path, "rb") as image_file:
            image_data = image_file.read()
            base64_image = base64.b64encode(image_data).decode("utf-8")
        
        # Create analysis message
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": """Analyze this bird's-eye view maze image and provide:

1. MAZE_STRUCTURE: Describe the overall maze layout, including:
   - Black line boundaries and pathways
   - Open areas and dead ends
   - Start and end zones (if visible)
   - Key landmarks or features

2. ROBOT_POSITION: Estimate where the robot is currently located:
   - Which section/area of the maze
   - Approximate coordinates relative to maze boundaries
   - Current heading direction

3. NAVIGATION_PATH: Suggest a safe path through the maze:
   - Key waypoints to reach
   - Areas to avoid (dead ends, narrow passages)
   - Recommended movement strategy

4. SAFETY_CONCERNS: Identify potential hazards:
   - Areas close to black line boundaries
   - Narrow passages that require careful navigation
   - Recommended speeds for different sections

Provide this analysis in a structured format that can be used for robot navigation planning."""
                    },
                    {
                        "type": "input_image",
                        "image_url": f"data:image/jpeg;base64,{base64_image}"
                    }
                ]
            }
        ]
        
        # Send to navigation agent for analysis
        result = Runner.run_sync(
            navigation_agent,
            messages,
            session=None  # Must be None for message lists
        )
        
        return f"✅ Maze Analysis Complete:\n\n{result.final_output}"
        
    except Exception as e:
        return f"Error analyzing maze layout: {str(e)}"

@function_tool
def plan_navigation_path_tool(target_description: str) -> str:
    """Plan a navigation path through the maze."""
    try:
        # This would use the maze analysis to create a detailed path
        # For now, return a basic planning structure
        plan = {
            "target": target_description,
            "current_position": navigation_state['current_position'],
            "strategy": "Use bird's-eye view analysis to plan safe path avoiding black lines",
            "safety_notes": "Monitor grayscale sensors for boundary detection",
            "calibration_reminder": "Speed 30 for 1s = 30cm, Speed 50 for 2.1s = 90°"
        }
        
        return f"Navigation plan created: {json.dumps(plan, indent=2)}"
    except Exception as e:
        return f"Error planning navigation path: {str(e)}"

def execute_navigation_step_tool(step_description: str, navigation_agent, session) -> str:
    """Execute a specific navigation step with safety monitoring."""
    try:
        # Check for boundary hits before executing
        if navigation_state['boundary_hit']:
            return f"⚠️ Cannot execute step - boundary hit detected from last action: {navigation_state['last_action']}"
        
        # Execute the step
        result = Runner.run_sync(
            navigation_agent,
            step_description,
            session=session
        )
        
        return f"Navigation step executed: {result.final_output}"
    except Exception as e:
        return f"Error executing navigation step: {str(e)}"

@function_tool
def check_boundary_status_tool() -> str:
    """Check if robot has hit a boundary and get details."""
    try:
        status = {
            "boundary_hit": navigation_state['boundary_hit'],
            "last_action": navigation_state['last_action'],
            "current_position": navigation_state['current_position'],
            "grayscale_monitoring": navigation_state['grayscale_monitoring']
        }
        
        if navigation_state['boundary_hit']:
            return f"🚨 BOUNDARY HIT DETECTED!\nLast action: {navigation_state['last_action']}\nStatus: {json.dumps(status, indent=2)}"
        else:
            return f"✅ No boundary hit detected. Status: {json.dumps(status, indent=2)}"
    except Exception as e:
        return f"Error checking boundary status: {str(e)}"

@function_tool
def update_position_tool(x: float, y: float, heading: float) -> str:
    """Update robot's estimated position."""
    try:
        navigation_state['current_position'] = {'x': x, 'y': y, 'heading': heading}
        return f"Position updated to: x={x}, y={y}, heading={heading}°"
    except Exception as e:
        return f"Error updating position: {str(e)}"

@function_tool
def get_navigation_status_tool() -> str:
    """Get comprehensive navigation status."""
    try:
        status = {
            "position": navigation_state['current_position'],
            "last_action": navigation_state['last_action'],
            "boundary_hit": navigation_state['boundary_hit'],
            "grayscale_monitoring": navigation_state['grayscale_monitoring'],
            "path_history": navigation_state['path_history'][-5:],  # Last 5 actions
            "calibration": {
                "forward_30cm": "Speed 30 for 1 second",
                "turn_90deg": "Speed 50 for 2.1 seconds"
            }
        }
        
        return json.dumps(status, indent=2)
    except Exception as e:
        return f"Error getting navigation status: {str(e)}"

# ============================================================================
# MAIN FUNCTION
# ============================================================================

def main():
    """Main function to run the maze navigation agent."""
    # Check for API key
    if not OPENAI_API_KEY:
        print("Error: OPENAI_API_KEY not found in keys.py")
        print("Please add your OpenAI API key to keys.py")
        sys.exit(1)
    
    # Initialize the maze navigation agent
    agent = MazeNavigationAgent()
    
    print("🤖 Maze Navigation Agent initialized!")
    print("Commands:")
    print("  'navigate' - Start maze navigation with command list")
    print("  'commands' - Get navigation commands without executing")
    print("  'execute [commands]' - Execute specific command list")
    print("  'correct' - Get course correction after boundary hit")
    print("  'status' - Check navigation status")
    print("  'boundary' - Check boundary hit status")
    print("  'position' - Get current position")
    print("  'quit' - Exit")
    print("  'reset' - Reset robot and position")
    print("-" * 50)
    
    try:
        while True:
            # Get user input
            user_input = input("Maze Agent: ").strip()
            
            if user_input.lower() == 'quit':
                agent.stop_grayscale_monitoring()
                break
            elif user_input.lower() == 'navigate':
                result = agent.navigate_maze("Navigate through the maze to find the exit")
                print(f"🎯 Navigation Result:\n{result}")
            elif user_input.lower() == 'commands':
                commands = agent.get_navigation_commands("Navigate through the maze to find the exit")
                if commands:
                    print(f"📋 Navigation Commands:\n{json.dumps(commands, indent=2)}")
                else:
                    print("❌ Failed to get navigation commands")
            elif user_input.lower().startswith('execute '):
                try:
                    commands_json = user_input[8:].strip()
                    commands = json.loads(commands_json)
                    result = agent.execute_command_list(commands)
                    print(f"🚀 Execution Result:\n{result}")
                except json.JSONDecodeError:
                    print("❌ Invalid JSON format for commands")
                except Exception as e:
                    print(f"❌ Error executing commands: {e}")
            elif user_input.lower() == 'correct':
                # Get course correction commands
                correction_prompt = """The robot hit a boundary. Please provide course correction commands as a JSON list."""
                result = Runner.run_sync(
                    agent.navigation_agent,
                    correction_prompt,
                    session=agent.session
                )
                print(f"🔄 Course Correction:\n{result.final_output}")
            elif user_input.lower() == 'status':
                status = agent.get_navigation_status()
                print(f"📊 Navigation Status:\n{json.dumps(status, indent=2)}")
            elif user_input.lower() == 'boundary':
                result = Runner.run_sync(
                    agent.navigation_agent,
                    "Check if robot has hit any boundaries",
                    session=agent.session
                )
                print(f"🚨 Boundary Check:\n{result.final_output}")
            elif user_input.lower() == 'position':
                result = Runner.run_sync(
                    agent.navigation_agent,
                    "Get current robot position and heading",
                    session=agent.session
                )
                print(f"📍 Position:\n{result.final_output}")
            elif user_input.lower() == 'reset':
                result = Runner.run_sync(
                    agent.navigation_agent,
                    "Reset robot and clear navigation state",
                    session=agent.session
                )
                print(f"🔄 Reset:\n{result.final_output}")
            else:
                # Process custom navigation request
                result = agent.navigate_maze(user_input)
                print(f"🎯 Navigation Result:\n{result}")
            
    except KeyboardInterrupt:
        print("\nExiting...")
        agent.stop_grayscale_monitoring()

if __name__ == "__main__":
    main()
