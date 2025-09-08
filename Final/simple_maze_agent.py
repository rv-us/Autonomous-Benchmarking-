"""
Simple Maze Navigation Agent for Picar-X Robot

Flow:
1. User passes in image of maze
2. Agent analyzes image, finds robot position and green exit
3. Agent returns list of commands based on calibration
4. Commands are executed with grayscale monitoring
5. If boundary hit, agent gets new image and recreates command list
6. Human resets robot to start position
"""

import os
import sys
import time
import threading
import base64
import json
from typing import List, Dict, Any
from agents import Agent, Runner
from agents import function_tool
from agents.memory import SQLiteSession
from PIL import Image
import io

# Import the primitives
from final_primitives import *

# Get OpenAI API key from environment variable
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    print("Error: OPENAI_API_KEY environment variable not set!")
    print("Please set it with: export OPENAI_API_KEY='your-key-here'")
    sys.exit(1)

# Global variables for execution state
execution_state = {
    'boundary_hit': False,
    'last_action': None,
    'current_commands': [],
    'execution_log': []
}

# Threading control
grayscale_thread = None
stop_grayscale_monitoring = threading.Event()

class SimpleMazeAgent:
    """Simple maze navigation agent with image analysis and command generation."""
    
    def __init__(self, session_id: str = "simple_maze"):
        self.session_id = session_id
        self.session = SQLiteSession(
            session_id=session_id,
            db_path="simple_maze_memory.db"
        )
        
        # Create the maze analysis agent
        self.maze_agent = self._create_maze_agent()
    
    def _create_maze_agent(self) -> Agent:
        """Create the maze analysis agent."""
        return Agent(
            name="Maze Analysis Agent",
            instructions="""You are a maze navigation specialist for a Picar-X robot. Your job is to analyze maze images and generate precise movement commands.

MOVEMENT CALIBRATION (CRITICAL):
- Speed 30 for 1 second = 30 centimeters forward
- Speed 50 for 2.1 seconds = 90 degrees turn (left or right)
- Speed 20 for 0.5 seconds = 15 centimeters forward
- Speed 40 for 1.4 seconds = 60 degrees turn

COMMAND FORMAT:
Return ONLY a JSON array of commands like this:
[
    {"action": "move_forward", "speed": 30, "duration": 1.0, "description": "Move forward 30cm"},
    {"action": "turn_right", "speed": 50, "duration": 2.1, "description": "Turn right 90 degrees"},
    {"action": "move_forward", "speed": 20, "duration": 0.5, "description": "Move forward 15cm"},
    {"action": "turn_left", "speed": 50, "duration": 1.4, "description": "Turn left 60 degrees"}
]

AVAILABLE ACTIONS:
- move_forward(speed, duration)
- move_backward(speed, duration) 
- turn_left(speed, duration)
- turn_right(speed, duration)
- set_dir_servo(angle) - for steering

ANALYSIS TASK:
When you receive a maze image, analyze it to:
1. Find the robot's current position in the maze
2. Locate the green highlighted exit area
3. Identify black line boundaries and pathways
4. Plan a safe route from robot to exit
5. Generate precise movement commands

SAFETY RULES:
- Avoid black line boundaries
- Use smaller movements near boundaries
- Plan conservative routes
- Consider robot's current position and heading

CRITICAL: Your response must be ONLY a valid JSON array starting with [ and ending with ]. Do not include any other text, explanations, or formatting. The response will be parsed directly as JSON.

Example of correct response format:
[{"action": "move_forward", "speed": 30, "duration": 1.0, "description": "Move forward 30cm"}]""",
            tools=[]
        )
    
    def analyze_maze_and_get_commands(self, image_path: str, boundary_context: str = None) -> List[Dict]:
        """Analyze maze image and return command list, with optional boundary context for course correction."""
        try:
            print(f"🔍 Analyzing maze image: {image_path}")
            if boundary_context:
                print(f"🔄 Using boundary context for course correction: {boundary_context}")
            
            # Read and encode image
            with open(image_path, "rb") as image_file:
                image_data = image_file.read()
                base64_image = base64.b64encode(image_data).decode("utf-8")
                print(f"📸 Image loaded: {len(image_data)} bytes, base64 length: {len(base64_image)}")
            
            # Create analysis prompt with boundary context if provided
            analysis_prompt = """Look at this maze image. Find the robot (small vehicle) and the green exit area. Create a JSON array of movement commands to navigate from the robot to the green exit, avoiding black lines.

Return ONLY this JSON format:
[{"action": "move_forward", "speed": 30, "duration": 1.0, "description": "Move forward 30cm"}]

Do not include any other text, explanations, or analysis. Only return the JSON array."""
            
            if boundary_context:
                analysis_prompt = f"""PREVIOUS ATTEMPT FAILED: {boundary_context}

Look at this maze image again. Find the robot and green exit. Create a NEW JSON array of movement commands, avoiding the area where the boundary was hit.

Return ONLY this JSON format:
[{"action": "move_forward", "speed": 20, "duration": 0.5, "description": "Move forward 15cm"}]

Do not include any other text. Only return the JSON array."""
            
            # Create message with image for direct analysis
            messages = [
                {
                    "role": "system",
                    "content": "You are a maze navigation robot. You MUST respond with ONLY a valid JSON array of movement commands. Do not provide explanations, analysis, or any other text. Only return the JSON array."
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": analysis_prompt
                        },
                        {
                            "type": "input_image",
                            "image_url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    ]
                }
            ]
            
            # Send image directly to agent for analysis
            print(f"🚀 Sending request to OpenAI API...")
            try:
                result = Runner.run_sync(
                    self.maze_agent,
                    messages,
                    session=None  # Must be None for message lists
                )
                print(f"✅ API call successful")
            except Exception as api_error:
                print(f"❌ API call failed: {api_error}")
                return []
            
            # Debug: Print the raw response
            print(f"🔍 Raw agent response: '{result.final_output}'")
            print(f"🔍 Response type: {type(result.final_output)}")
            print(f"🔍 Response length: {len(str(result.final_output))}")
            
            # Clean the response - remove any text before/after JSON
            response_text = result.final_output.strip()
            
            # Try to find JSON array in the response
            json_start = response_text.find('[')
            json_end = response_text.rfind(']') + 1
            
            if json_start != -1 and json_end > json_start:
                json_text = response_text[json_start:json_end]
                print(f"🔍 Extracted JSON: {json_text}")
            else:
                print(f"❌ No JSON array found in response")
                return []
            
            # Parse JSON response
            commands = json.loads(json_text)
            print(f"📋 Generated {len(commands)} commands")
            return commands
            
        except Exception as e:
            print(f"❌ Error analyzing maze: {e}")
            return []
    
    def execute_commands_with_monitoring(self, commands: List[Dict]) -> Dict:
        """Execute command list with grayscale monitoring."""
        try:
            print(f"🚀 Executing {len(commands)} commands with monitoring...")
            
            execution_log = []
            successful_commands = 0
            
            for i, command in enumerate(commands):
                print(f"\n🔄 Command {i+1}/{len(commands)}: {command['action']} - {command['description']}")
                
                # Reset boundary hit flag
                execution_state['boundary_hit'] = False
                execution_state['last_action'] = command
                
                # Start monitoring for this command
                self.start_grayscale_monitoring()
                
                try:
                    # Execute the command
                    result = self.execute_single_command(command)
                    
                    # Check if boundary was hit during execution
                    if execution_state['boundary_hit']:
                        print(f"🚨 BOUNDARY HIT during command {i+1}!")
                        execution_log.append({
                            'command_index': i,
                            'command': command,
                            'result': result,
                            'success': False,
                            'boundary_hit': True,
                            'last_action': execution_state['last_action']
                        })
                        break
                    else:
                        successful_commands += 1
                        execution_log.append({
                            'command_index': i,
                            'command': command,
                            'result': result,
                            'success': True,
                            'boundary_hit': False
                        })
                        print(f"✅ Command {i+1} completed successfully")
                        
                except Exception as e:
                    execution_log.append({
                        'command_index': i,
                        'command': command,
                        'result': f"Error: {str(e)}",
                        'success': False,
                        'boundary_hit': execution_state['boundary_hit']
                    })
                    print(f"❌ Command {i+1} failed: {e}")
                    break
                
                finally:
                    # Stop monitoring after each command
                    self.stop_grayscale_monitoring()
                    
                    # Ensure robot is completely stopped
                    try:
                        reset()
                    except:
                        pass
                    
                    # Wait for command to fully complete
                    time.sleep(1.0)  # Longer pause between commands
            
            return {
                'success': not execution_state['boundary_hit'],
                'successful_commands': successful_commands,
                'total_commands': len(commands),
                'boundary_hit': execution_state['boundary_hit'],
                'execution_log': execution_log,
                'last_action': execution_state['last_action']
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'execution_log': []
            }
    
    def execute_single_command(self, command: Dict) -> str:
        """Execute a single command with proper sequencing."""
        action = command.get('action')
        speed = command.get('speed', 30)
        duration = command.get('duration', 1.0)
        angle = command.get('angle', 0)
        
        try:
            # Ensure robot is stopped before starting new command
            reset()
            time.sleep(0.1)  # Brief pause to ensure stop is complete
            
            if action == 'move_forward':
                move_forward(speed, duration)
                return f"Moved forward at speed {speed} for {duration}s"
            elif action == 'move_backward':
                move_backward(speed, duration)
                return f"Moved backward at speed {speed} for {duration}s"
            elif action == 'turn_left':
                turn_left(speed, duration)
                return f"Turned left at speed {speed} for {duration}s"
            elif action == 'turn_right':
                turn_right(speed, duration)
                return f"Turned right at speed {speed} for {duration}s"
            elif action == 'set_dir_servo':
                set_dir_servo(angle)
                return f"Set steering servo to {angle} degrees"
            else:
                return f"Unknown action: {action}"
                
        except Exception as e:
            # Ensure robot is stopped on error
            try:
                reset()
            except:
                pass
            raise e
    
    def start_grayscale_monitoring(self):
        """Start grayscale monitoring for boundary detection."""
        global grayscale_thread, stop_grayscale_monitoring
        
        if grayscale_thread and grayscale_thread.is_alive():
            return
        
        stop_grayscale_monitoring.clear()
        
        def monitor_grayscale():
            """Monitor grayscale sensors for black line detection."""
            while not stop_grayscale_monitoring.is_set():
                try:
                    grayscale_values = get_grayscale()
                    
                    # Check for black line detection
                    black_line_threshold = 1000
                    if any(value < black_line_threshold for value in grayscale_values):
                        print("🚨 BLACK LINE DETECTED - BOUNDARY HIT!")
                        execution_state['boundary_hit'] = True
                        
                        # Emergency stop
                        try:
                            reset()
                        except:
                            pass
                        
                        # Log boundary hit
                        print(f"🚨 Boundary hit during action: {execution_state['last_action']}")
                        break
                    
                    time.sleep(0.1)  # Check every 100ms
                    
                except Exception as e:
                    print(f"⚠️ Grayscale monitoring error: {e}")
                    time.sleep(0.5)
        
        grayscale_thread = threading.Thread(target=monitor_grayscale, daemon=True)
        grayscale_thread.start()
    
    def stop_grayscale_monitoring(self):
        """Stop grayscale monitoring."""
        global stop_grayscale_monitoring
        stop_grayscale_monitoring.set()
    
    def store_attempt_result(self, attempt: int, commands: List[Dict], execution_result: Dict, context: str):
        """Store attempt result in memory for learning."""
        try:
            # Store in session memory
            memory_entry = {
                'attempt': attempt,
                'commands': commands,
                'execution_result': execution_result,
                'context': context,
                'timestamp': time.time()
            }
            
            # Send to agent for memory storage
            result = Runner.run_sync(
                self.maze_agent,
                f"Store this navigation attempt result in memory: {json.dumps(memory_entry)}",
                session=self.session
            )
            
            print(f"💾 Stored attempt {attempt} result in memory")
            
        except Exception as e:
            print(f"⚠️ Error storing attempt result: {e}")

# ============================================================================
# MAZE ANALYSIS (Built into agent instructions)
# ============================================================================

# ============================================================================
# MAIN EXECUTION FUNCTIONS
# ============================================================================

def run_maze_navigation(image_path: str, max_attempts: int = 3) -> Dict:
    """Main function to run maze navigation with image and course correction."""
    try:
        # Initialize agent
        agent = SimpleMazeAgent()
        
        print(f"🎯 Starting maze navigation with image: {image_path}")
        print(f"🔄 Maximum attempts: {max_attempts}")
        
        attempt = 1
        boundary_context = None
        
        while attempt <= max_attempts:
            print(f"\n🔄 === ATTEMPT {attempt}/{max_attempts} ===")
            
            # Step 1: Analyze maze and get commands (with boundary context if retry)
            commands = agent.analyze_maze_and_get_commands(image_path, boundary_context)
            
            if not commands:
                return {
                    'success': False,
                    'error': 'Failed to generate navigation commands',
                    'attempts': attempt,
                    'commands': []
                }
            
            # Step 2: Execute commands with monitoring
            execution_result = agent.execute_commands_with_monitoring(commands)
            
            # Step 3: Check if successful or boundary hit
            if execution_result['boundary_hit']:
                print(f"🚨 Boundary hit on attempt {attempt}")
                
                # Create boundary context for next attempt
                failed_command = execution_result['execution_log'][-1] if execution_result['execution_log'] else None
                if failed_command:
                    boundary_context = f"Command {failed_command['command_index'] + 1} failed: {failed_command['command']['action']} - {failed_command['command']['description']}. Robot hit black line boundary during this movement."
                else:
                    boundary_context = f"Attempt {attempt} failed: Robot hit black line boundary during execution."
                
                print(f"📝 Boundary context for next attempt: {boundary_context}")
                
                # Store failure in memory
                agent.store_attempt_result(attempt, commands, execution_result, boundary_context)
                
                if attempt < max_attempts:
                    print(f"🔄 Preparing for attempt {attempt + 1} with course correction...")
                    print("👤 Human should reset robot to start position and take new image")
                    input("Press Enter when ready for next attempt...")
                else:
                    print("❌ Maximum attempts reached")
                    return {
                        'success': False,
                        'boundary_hit': True,
                        'attempts': attempt,
                        'commands': commands,
                        'execution_result': execution_result,
                        'message': f'Failed after {max_attempts} attempts. Last boundary context: {boundary_context}'
                    }
            else:
                print("✅ Navigation completed successfully!")
                agent.store_attempt_result(attempt, commands, execution_result, "Success")
                return {
                    'success': True,
                    'boundary_hit': False,
                    'attempts': attempt,
                    'commands': commands,
                    'execution_result': execution_result,
                    'message': f'Navigation completed successfully on attempt {attempt}!'
                }
            
            attempt += 1
            
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'attempts': attempt if 'attempt' in locals() else 0,
            'commands': []
        }

def main():
    """Main function for testing."""
    if len(sys.argv) != 2:
        print("Usage: python simple_maze_agent.py <image_path>")
        print("Example: python simple_maze_agent.py maze_photo.jpg")
        sys.exit(1)
    
    image_path = sys.argv[1]
    
    if not os.path.exists(image_path):
        print(f"Error: Image file '{image_path}' not found!")
        sys.exit(1)
    
    # Run maze navigation
    result = run_maze_navigation(image_path)
    
    print("\n" + "="*50)
    print("MAZE NAVIGATION RESULT")
    print("="*50)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
