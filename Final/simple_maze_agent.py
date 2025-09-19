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
            model="gpt-5",
            instructions="""You are a maze navigation specialist for a Picar-X robot. Your job is to analyze maze images and generate precise movement commands.

MOVEMENT CALIBRATION (CRITICAL):
- Speed 30 for 1 second = 30 centimeters forward
- Speed 30 for 2.13 seconds = 90 degrees turn (right)
- Speed 30 for 3.15 seconds = 90 degrees turn (left)
- Speed 20 for 0.5 seconds = 15 centimeters forward
- Speed 40 for 1.4 seconds = 60 degrees turn

ROBOT DIMENSIONS:
- The robot car is 30 centimeters long
- Use this as a reference scale to estimate distances in the maze
- When calculating movement distances, consider the robot's length for precise navigation

MAZE DIMENSIONS (if provided in image):
- Look for measurement labels in the maze image (e.g., "71 cm", "83 cm")
- Use these measurements to calculate precise movement distances
- Scale your movement commands based on the actual maze dimensions
- keep in mind that the robot moves a little forward in the direction it is turning, and that the dimensions are end 2 end of the maze
- If measurements are visible, use them to determine exact distances for each movement segment

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

ROBOT ORIENTATION IN MAZE:
The robot car is positioned in the BOTTOM-LEFT corner of the maze, facing UP (north direction).
- The robot's front (sensor end) points toward the Top side of the image
- The robot's rear (circuit board with lights) points toward the LEFT side of the image

DIRECTIONAL REFERENCE (from robot's perspective):
When the robot faces UP (current position):
- "RIGHT" for the robot = RIGHT side of the image (east direction)
- "LEFT" for the robot = LEFT side of the image (west direction)  
- "FORWARD" for the robot = TOP of the image (north direction)
- "BACKWARD" for the robot = BOTTOM of the image (south direction)

NAVIGATION HINTS:
- Look for BLUE ARROWS in the maze - these indicate the suggested escape route
- COUNT the number of blue arrows from the robot's starting position
- ANALYZE the direction each blue arrow is pointing
- The YELLOW HIGHLIGHTED area in the top-left corner is the exit
- Use the blue arrow directions to generate movement commands
- Each blue arrow represents a movement segment or turn

MOVEMENT STRATEGY - KEEP IT SIMPLE:
- Identify the MINIMUM number of moves required to escape
- NO small adjustments or micro-movements
- Each movement should be ONE complete action (either a full turn OR a full forward movement)
- If an arrow points in a different direction than the robot is currently facing, the robot must TURN FIRST, then MOVE
- Follow the blue arrows in sequence: each arrow = one movement command
- Plan the most direct route with the fewest possible commands

ANALYSIS TASK - CHAIN OF THOUGHT REASONING:
When you receive a maze image, follow this step-by-step reasoning process:

STEP 1 - OBSERVATION:
1. Find the robot's current position and orientation in the maze
2. Locate the yellow highlighted exit area
3. Identify black line boundaries and pathways
4. Note any obstacles or narrow passages

STEP 2 - SPATIAL ANALYSIS:
1. Calculate approximate distances from robot to exit
2. Identify the general direction the robot needs to travel
3. Map out the available pathways and dead ends
4. Consider the robot's current facing direction

STEP 3 - ROUTE PLANNING:
1. Follow the blue arrows in sequence from robot to exit
2. For each arrow, determine if robot needs to turn first before moving in that direction
3. Plan the MINIMUM number of moves: each arrow = one command (turn OR move, not both)
4. If arrow direction differs from robot's current facing, add a turn command first
5. Keep movements simple and direct - no small adjustments

STEP 4 - MOVEMENT CALCULATION:
1. Convert your planned route into specific movement commands
2. Use the calibration data to calculate precise speeds and durations
3. Consider the robot's perspective for left/right/forward/backward
4. Add safety margins and conservative movements

STEP 5 - COMMAND GENERATION:
1. Generate the final JSON array of movement commands
2. Ensure each command is properly calibrated
3. Include descriptive text for each movement
4. Verify the sequence will reach the exit safely

REASONING FORMAT - MANDATORY:
You MUST provide detailed reasoning before generating commands. Follow this EXACT format:

REASONING:
STEP 1 - OBSERVATION:
- Robot position: [robot is in bottom-left corner, facing UP (north)]
- Exit location: [describe where the yellow highlighted exit is]
- Blue arrow count: [count the total number of blue arrows from robot]
- Blue arrow directions: [carefully examine each arrow head direction: Arrow 1 points X, Arrow 2 points Y, etc. Look at the arrow head, not the path]
- Maze dimensions: [look for measurement labels like "x cm", "y cm" and note their positions]
- Boundaries: [describe black lines and obstacles]
- Pathways: [describe available routes]

STEP 2 - SPATIAL ANALYSIS:
- Distance to exit: [rough estimate]
- Direction needed: [which way robot needs to go]
- Available paths: [describe possible routes]
- Current facing: [robot's current orientation]

STEP 3 - ROUTE PLANNING:
- Blue arrow sequence: [list the exact sequence of movements based on blue arrows]
- Command mapping: [map each blue arrow to ONE command: Arrow 1 = move_forward, Arrow 2 = turn_right, etc.]
- Turn-then-move logic: [if arrow points different direction than robot faces, add turn command first]
- Minimum moves: [count total commands needed - should equal number of arrows]
- Simple movements: [no small adjustments, each command is complete action]

STEP 4 - MOVEMENT CALCULATION:
- Command 1: [action, speed, duration, reasoning]
- Command 2: [action, speed, duration, reasoning]
- Command 3: [action, speed, duration, reasoning]
- Safety considerations: [any adjustments for safety]

STEP 5 - VERIFICATION:
- Arrow verification: [double-check each arrow direction matches the generated commands]
- Route check: [verify this will reach the exit]
- Safety check: [verify no boundary violations]
- Calibration check: [verify speeds and durations are correct]

SAFETY RULES:
- Avoid black line boundaries
- Use smaller movements near boundaries
- Plan conservative routes
- Consider robot's current position and heading

BOUNDARY BEHAVIOR:
- The robot will AUTOMATICALLY STOP if it hits a black line boundary
- When a boundary is hit, the robot stops immediately and the attempt fails
- The robot must be manually reset to the starting position for the next attempt

COURSE CORRECTION STRATEGY:
- If the robot hit a boundary during a "move_forward" command, reduce the duration for that movement in the next attempt
- If the robot hit a boundary during a "turn_left" or "turn_right" command, the turn may be too sharp - consider adjusting the angle or using smaller movements
- If the robot hit a boundary during "move_backward", reduce the duration or avoid that movement
- Use the boundary context from the previous attempt to plan a safer route
- Consider alternative paths that avoid the area where the boundary was hit
- When in doubt, use smaller, more conservative movements

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
            analysis_prompt = """Look at this maze image and follow the detailed 5-step reasoning process.

STEP 1 - OBSERVATION: Find the robot (small vehicle) in the bottom-left corner facing UP, the yellow exit area in the top-left, and COUNT the BLUE ARROWS. Look for any measurement labels like "x cm" or "y cm" that indicate maze dimensions. Carefully analyze the direction each blue arrow is pointing - look at the arrow head direction, not just the general path.

STEP 2 - SPATIAL ANALYSIS: Calculate distances and determine the general direction needed. Note that the robot is facing UP (north).

STEP 3 - ROUTE PLANNING: Follow the blue arrows in sequence. For each arrow, determine if robot needs to turn first before moving in that direction. Plan the MINIMUM number of moves - each arrow = one command.

STEP 4 - MOVEMENT CALCULATION: Convert the blue arrow sequence into specific movement commands. If an arrow points in a different direction than robot faces, add a turn command first, then the movement command.

STEP 5 - VERIFICATION: Ensure the route will reach the yellow exit safely.

Provide your reasoning in the exact format specified in the instructions, then return the JSON array of movement commands.

JSON format:
[{{"action": "move_forward", "speed": 30, "duration": 1.0, "description": "Move forward 30cm"}}]"""
            
            if boundary_context:
                analysis_prompt = f"""PREVIOUS ATTEMPT FAILED: {boundary_context}

The robot automatically stopped when it hit a black line boundary. You must create a NEW route that avoids this failure point.

COURSE CORRECTION INSTRUCTIONS:
- If the failure was during "move_forward", reduce the duration for that movement (e.g., from 2.0s to 1.0s)
- If the failure was during a turn, consider using smaller movements or a different approach
- Plan a safer route that avoids the area where the boundary was hit
- Use more conservative movements near boundaries

Look at this maze image again and follow the detailed 5-step reasoning process to create a NEW route.

STEP 1 - OBSERVATION: Find the robot and yellow exit. Identify where the previous attempt failed and what boundaries to avoid.

STEP 2 - SPATIAL ANALYSIS: Recalculate distances and determine a different approach that avoids the failure point.

STEP 3 - ROUTE PLANNING: Plan an alternative route that avoids the failure point. Consider using smaller movements.

STEP 4 - MOVEMENT CALCULATION: Convert your new plan into specific movement commands with reduced durations for safety.

STEP 5 - VERIFICATION: Ensure the new route will reach the exit safely without hitting boundaries.

Provide your reasoning in the exact format specified in the instructions, then return the JSON array of movement commands.

JSON format:
[{{"action": "move_forward", "speed": 20, "duration": 0.5, "description": "Move forward 15cm"}}]"""
            
            # Create message with image for direct analysis
            messages = [
                {
                    "role": "system",
                    "content": "You are a maze navigation robot. You MUST follow the detailed 5-step reasoning process exactly as specified in the instructions. Provide your reasoning in the exact format required, then provide a valid JSON array of movement commands. Do not skip any steps or provide abbreviated reasoning."
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
            
            # Clean the response
            response_text = result.final_output.strip()
            
            # Extract reasoning if present
            reasoning_start = response_text.find('REASONING:')
            if reasoning_start != -1:
                reasoning_end = response_text.find('[', reasoning_start)
                if reasoning_end != -1:
                    reasoning = response_text[reasoning_start:reasoning_end].strip()
                    print(f"🧠 REASONING: {reasoning}")
                else:
                    print("🧠 REASONING: Found reasoning marker but no JSON array")
            else:
                print("🧠 REASONING: No reasoning provided")
            
            # Try to find JSON array in the response
            json_start = response_text.find('[')
            json_end = response_text.rfind(']') + 1
            
            if json_start != -1 and json_end > json_start:
                json_text = response_text[json_start:json_end]
                print(f"🔍 Extracted JSON: {json_text}")
                
                try:
                    commands = json.loads(json_text)
                    print(f"📋 Generated {len(commands)} commands")
                    return commands
                except json.JSONDecodeError as json_error:
                    print(f"❌ JSON parsing error: {json_error}")
                    return []
            else:
                print(f"❌ No JSON array found in response")
                return []
            
        except Exception as e:
            print(f"❌ Error analyzing maze: {e}")
            return []
    
    def execute_commands_with_monitoring(self, commands: List[Dict]) -> Dict:
        """Execute command list with continuous grayscale monitoring like the examples."""
        try:
            print(f"🚀 Executing {len(commands)} commands with monitoring...")
            
            execution_log = []
            successful_commands = 0
            
            for i, command in enumerate(commands):
                print(f"\n🔄 Command {i+1}/{len(commands)}: {command['action']} - {command['description']}")
                
                # Reset boundary hit flag
                execution_state['boundary_hit'] = False
                execution_state['last_action'] = command
                
                try:
                    # Execute command with continuous monitoring (like cliff detection example)
                    result = self.execute_command_with_continuous_monitoring(command)
                    
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
                    # Ensure robot is completely stopped
                    try:
                        reset()
                    except:
                        pass
                    
                    # Wait between commands
                    time.sleep(0.5)
            
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
    
    def execute_command_with_continuous_monitoring(self, command: Dict) -> str:
        """Execute a single command with continuous grayscale monitoring like cliff detection example."""
        action = command.get('action')
        speed = command.get('speed', 30)
        duration = command.get('duration', 1.0)
        angle = command.get('angle', 0)
        
        try:
            # Ensure robot is stopped before starting
            reset()
            time.sleep(0.1)
            
            # Get start time for duration tracking
            start_time = time.time()
            
            # Handle different actions
            if action == 'move_forward':
                px = get_picarx()
                px.forward(speed)
                
                # Continuous monitoring loop for forward movement
                while time.time() - start_time < duration:
                    grayscale_values = get_grayscale()
                    black_line_threshold = 200
                    
                    if any(value < black_line_threshold for value in grayscale_values):
                        print("🚨 BLACK LINE DETECTED - BOUNDARY HIT!")
                        execution_state['boundary_hit'] = True
                        px.stop()
                        return f"Boundary hit during {action}"
                    
                    time.sleep(0.05)  # 50ms check interval
                
                px.stop()
                return f"Completed {action} at speed {speed} for {duration}s"
                
            elif action == 'move_backward':
                px = get_picarx()
                px.backward(speed)
                
                # Continuous monitoring loop for backward movement
                while time.time() - start_time < duration:
                    grayscale_values = get_grayscale()
                    black_line_threshold = 1000
                    
                    if any(value < black_line_threshold for value in grayscale_values):
                        print("🚨 BLACK LINE DETECTED - BOUNDARY HIT!")
                        execution_state['boundary_hit'] = True
                        px.stop()
                        return f"Boundary hit during {action}"
                    
                    time.sleep(0.05)  # 50ms check interval
                
                px.stop()
                return f"Completed {action} at speed {speed} for {duration}s"
                
            elif action == 'turn_left':
                # Use your in-place turn function (includes its own timing and monitoring)
                turn_left(speed, duration)
                return f"Turned left at speed {speed} for {duration}s"
                
            elif action == 'turn_right':
                # Use your in-place turn function (includes its own timing and monitoring)
                turn_right(speed, duration)
                return f"Turned right at speed {speed} for {duration}s"
                
            elif action == 'set_dir_servo':
                px = get_picarx()
                px.set_dir_servo_angle(angle)
                return f"Set steering servo to {angle} degrees"
            else:
                return f"Unknown action: {action}"
            
        except Exception as e:
            # Ensure robot is stopped on error
            try:
                px = get_picarx()
                px.stop()
            except:
                pass
            raise e
    
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
    
    # Grayscale monitoring is now handled in execute_command_with_continuous_monitoring
    # No separate threading needed - follows the cliff detection example pattern
    
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
