# Picar-X Smart Agent

A simplified yet powerful agent that combines the best of both worlds: the simplicity of the basic agent with the memory and planning capabilities of the advanced agent.

## 🎯 Key Features

- **Automatic Decision Making**: The agent automatically decides whether to act immediately or create a plan
- **Memory Persistence**: SQLite-based memory that persists across sessions
- **Three-Agent Architecture**: Orchestrator, Judge, and Action agents working together
- **Simplified Interface**: Clean, easy-to-understand API
- **Real-time State Tracking**: All agents have access to current servo angles and sensor readings

## 🏗️ Architecture

### 1. Orchestrator Agent
- **Purpose**: Analyzes user requests and decides the best approach
- **Decision Logic**:
  - **IMMEDIATE**: Simple commands like "Drive forward", "Turn left 20 degrees"
  - **NEEDS PLAN**: Complex tasks like "Explore the room", "Navigate around obstacles"
- **Tools**: Robot state monitoring for context-aware decisions

### 2. Judge Agent
- **Purpose**: Monitors plan progress and provides guidance
- **Capabilities**:
  - Check current plan status
  - Update progress tracking
  - Assess current robot state
  - Provide next-step guidance
- **Tools**: Planning tools + robot state + sensors (ultrasound, grayscale, camera)

### 3. Action Agent
- **Purpose**: Executes immediate commands and plan steps
- **Capabilities**: All robot control functions (movement, servos, sensors, etc.)
- **Tools**: Complete set of hardware control tools + robot state monitoring

## 🚀 Usage

### Basic Usage

```python
from picarx_agent_smart import PicarXSmartAgent

# Initialize the agent
agent = PicarXSmartAgent()

# Process a request (agent automatically decides approach)
result = agent.process_request("Drive forward at speed 30")
print(result)

# Check plan progress
progress = agent.check_plan_progress()
print(progress)

# Get current robot state
robot_state = agent.get_current_robot_state()
print(robot_state)

# Execute a specific plan step
step_result = agent.execute_plan_step("Take a picture")
print(step_result)
```

### Interactive Mode

```bash
python picarx_agent_smart.py
```

**Available Commands:**
- `quit` - Exit the program
- `reset` - Reset the robot
- `state` - Check current robot state (servos, sensors)
- `capture` - Take a photo using the camera
- `analyze [filename]` - Analyze an image file using GPT-4o vision
- `see` - Take photo and analyze what you see
- `status` - Check current plan status
- `progress` - Get detailed progress report
- `execute: [step]` - Execute a specific plan step

### Example Script

```bash
python example_smart_agent.py
```

## 🔄 How It Works

### 1. Request Processing Flow

```
User Request → Orchestrator → Decision → Action/Planning
                ↓
        IMMEDIATE or NEEDS PLAN
                ↓
        Action Agent or Judge Agent
```

### 2. Decision Examples

| Request | Decision | Action |
|---------|----------|---------|
| "Drive forward" | IMMEDIATE | Execute immediately |
| "Turn left 45°" | IMMEDIATE | Execute immediately |
| "Explore the room" | NEEDS PLAN | Create plan, use judge |
| "Find the exit" | NEEDS PLAN | Create plan, use judge |

### 3. Memory Persistence

- **Session-based**: Each agent instance maintains its own memory
- **SQLite Storage**: Persistent across program restarts
- **Context Awareness**: Agents remember previous conversations and actions

### 4. Servo Angle Tracking

- **Real-time Monitoring**: All servo angles are continuously tracked
- **Context-Aware Decisions**: Agents know current positions before making decisions
- **Smart Execution**: Commands consider current servo state for optimal execution
- **State Persistence**: Servo positions are remembered across sessions

## 🛠️ Tool Functions

### Movement Tools
- `drive_forward_tool(speed, duration)`
- `drive_backward_tool(speed, duration)`
- `turn_left_tool(angle, speed, duration)`
- `turn_right_tool(angle, speed, duration)`
- `stop_tool()`

### Servo Tools
- `set_dir_servo_tool(angle)`
- `set_cam_pan_servo_tool(angle)`
- `set_cam_tilt_servo_tool(angle)`
- `set_motor_speed_tool(motor_id, speed)`

### Sensor Tools
- `get_ultrasound_tool()`
- `get_grayscale_tool()`
- `capture_image_tool(filename)`
- `analyze_image_tool(image_path, analysis_prompt)` - Analyze images using GPT-4o vision
- `captureAndAnalyze_tool(filename, analysis_prompt)` - Capture and analyze in one step
- `play_sound_tool(filename, volume)`

### Planning Tools
- `create_plan_tool(task_description)`
- `check_plan_status_tool()`
- `update_plan_progress_tool(step_description, completed)`

### State Monitoring Tools
- `get_robot_state_tool()` - Get current servo angles and sensor readings

## 📊 Plan Management

### Plan Structure
```json
{
  "task": "Explore the room and find the exit",
  "current_step": 2,
  "total_steps": 5,
  "history": [
    {
      "step": 1,
      "description": "Take initial photo",
      "completed": true,
      "timestamp": 1234567890
    }
  ],
  "status": "in_progress"
}
```

### Progress Tracking
- Automatic step counting
- Timestamp tracking
- Completion status
- Action history

## 🔧 Configuration

### Session Management
```python
# Custom session ID
agent = PicarXSmartAgent(session_id="my_custom_session")

# Custom database path
agent = PicarXSmartAgent(session_id="picarx_main")
# Database will be saved as "picarx_main.db"
```

### Memory Database
- **Default**: `picarx_smart_memory.db`
- **Location**: Current working directory
- **Format**: SQLite database
- **Persistence**: Survives program restarts

## 🎮 Example Scenarios

### Scenario 1: Simple Movement
```
User: "Drive forward at speed 30"
Orchestrator: "IMMEDIATE: Drive forward at speed 30"
Action Agent: Executes drive_forward_tool(30)
Result: "✅ Action completed: Started driving forward at speed 30"
```

### Scenario 2: Complex Task
```
User: "Explore the room and find the exit"
Orchestrator: "NEEDS PLAN: Explore room to find exit"
Action Agent: Creates plan
Judge Agent: Provides status and guidance
Result: Plan created with next steps
```

### Scenario 3: Plan Execution
```
User: "execute: Take a picture of the current view"
Judge Agent: Updates progress
Action Agent: Executes capture_image_tool
Result: "📋 Step executed: Image captured and saved as capture.jpg"
```

### Scenario 4: Servo Angle Awareness
```
User: "Turn left 20 degrees"
Orchestrator: Checks current robot state (steering servo at -15°)
Decision: "IMMEDIATE: Turn left 20 degrees from current position"
Action Agent: Executes turn_left_tool(20) → goes to -35°
Result: "✅ Action completed: Turned left 20 degrees from -15° to -35°"
```

### Scenario 5: Image Analysis and Vision
```
User: "Take a photo and tell me what you see"
Orchestrator: "IMMEDIATE: Capture and analyze image"
Action Agent: Executes captureAndAnalyze_tool()
Result: "Image captured and analyzed: [GPT-4o vision analysis]"
```

### Scenario 6: Vision-Guided Navigation
```
User: "Find the red object in the room"
Orchestrator: "NEEDS PLAN: Navigate to find red object using vision"
Action Agent: Creates plan with image capture steps
Judge Agent: Monitors progress, suggests when to take photos
Result: Systematic search using visual feedback
```

## 🚨 Safety Features

- **Speed Limits**: All movement functions capped at 0-100 range
- **Angle Constraints**: Servo limits prevent hardware damage
- **Emergency Stop**: `reset()` function for safe shutdown
- **Obstacle Detection**: Ultrasonic sensor integration

## 🔍 Troubleshooting

### Common Issues

1. **API Key Not Found**
   ```
   Error: OPENAI_API_KEY not found in keys.py
   ```
   Solution: Add your OpenAI API key to `keys.py`

2. **Memory Database Issues**
   ```
   Error: database is locked
   ```
   Solution: Ensure only one instance is running, or use different session IDs

3. **Agent Not Responding**
   ```
   Error: No response from agent
   ```
   Solution: Check internet connection and API key validity

### Debug Mode

Enable verbose logging by modifying the agent:
```python
# Add debug prints
print(f"Debug: Orchestrator decision: {decision}")
print(f"Debug: Action result: {result}")
```

## 📈 Benefits Over Previous Agents

### vs. Basic Agent (`picarx_agent.py`)
- ✅ Memory persistence
- ✅ Automatic planning for complex tasks
- ✅ Progress tracking
- ✅ Context awareness

### vs. Advanced Agent (`picarx_agent_advanced.py`)
- ✅ Simpler architecture
- ✅ Cleaner separation of concerns
- ✅ Easier to understand and modify
- ✅ Less code complexity
- ✅ Better error handling

## 🎯 Best Practices

1. **Use Clear Commands**: Be specific about what you want the robot to do
2. **Monitor Progress**: Use `status` and `progress` commands to track complex tasks
3. **Session Management**: Use meaningful session IDs for different use cases
4. **Error Handling**: Always check the return values for error messages
5. **Safety First**: Use appropriate speeds and always have a reset command ready
6. **Vision Integration**: Use image analysis for better navigation and object recognition
7. **Image Quality**: Ensure good lighting and camera positioning for best analysis results

## 🖼️ Image Analysis Capabilities

The smart agent now includes advanced vision capabilities using GPT-4o:

### Image Tools
- **`capture_image_tool(filename)`**: Take a photo and save it
- **`analyze_image_tool(image_path, prompt)`**: Analyze existing images with custom prompts
- **`captureAndAnalyze_tool(filename, prompt)`**: Capture and analyze in one efficient step

### Vision-Enhanced Decision Making
- **Obstacle Detection**: Analyze images to identify obstacles and safe paths
- **Object Recognition**: Find and identify objects in the environment
- **Navigation Assistance**: Use visual feedback for better movement decisions
- **Task Verification**: Confirm task completion through visual inspection

### Example Vision Commands
```bash
# Take a photo
capture

# Analyze what you see
see

# Analyze specific image file
analyze my_photo.jpg

# Complex vision tasks
"Find the red ball in the room"
"Navigate around the chair I can see"
"Take a picture and tell me if the path is clear"
```

## 🔮 Future Enhancements

- **Voice Integration**: Add speech recognition and TTS
- **Advanced Vision**: Multi-camera support and real-time video analysis
- **Learning**: Improve decision-making based on past experiences
- **Multi-Robot**: Support for coordinating multiple robots
- **Web Interface**: Browser-based control panel
- **Gesture Recognition**: Understand human gestures and commands

## 📚 Related Files

- `picarx_agent_smart.py` - Main smart agent implementation
- `example_smart_agent.py` - Usage examples
- `picarx_primitives.py` - Hardware control functions
- `keys.py` - API key configuration
- `requirements.txt` - Python dependencies

This smart agent provides the perfect balance between simplicity and capability, making it ideal for both educational use and research applications.
