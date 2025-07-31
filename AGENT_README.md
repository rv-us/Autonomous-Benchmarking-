# Picar-X OpenAI Agents SDK Agent

This project implements a basic OpenAI Agents SDK agent that can control a SunFounder Picar-X robot using the functions from `picarx_primitives.py`.

## Features

The agent can control the following aspects of the Picar-X robot:

### Movement Control
- `drive_forward(speed, duration)` - Drive forward at specified speed
- `drive_backward(speed, duration)` - Drive backward at specified speed
- `turn_left(angle, speed, duration)` - Turn left with steering
- `turn_right(angle, speed, duration)` - Turn right with steering
- `stop()` - Stop all motors

### Servo Control
- `set_dir_servo(angle)` - Set steering servo angle
- `set_cam_pan_servo(angle)` - Set camera pan servo angle
- `set_cam_tilt_servo(angle)` - Set camera tilt servo angle
- `set_motor_speed(motor_id, speed)` - Set individual motor speed

### Sensors
- `get_ultrasound()` - Get distance from ultrasonic sensor
- `get_grayscale()` - Get grayscale sensor readings

### Camera
- `capture_image(filename)` - Capture and save an image

### Audio
- `play_sound(filename, volume)` - Play sound through speaker

### Safety
- `reset()` - Reset all servos to 0 and stop motors

## Setup

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure API Key**
   Edit `keys.py` and add your OpenAI API key:
   ```python
   OPENAI_API_KEY = "your-api-key-here"
   ```

3. **Ensure Picar-X Hardware is Connected**
   - Make sure your Picar-X robot is properly connected
   - Ensure all sensors and motors are working

## Usage

### Interactive Mode (Keyboard Input)

Run the agent in interactive mode with keyboard input:

```bash
python picarx_agent.py
```

This will start an interactive chat session where you can type commands like:
- "Drive forward at speed 30 for 2 seconds"
- "Turn left 20 degrees"
- "What's the distance from the ultrasonic sensor?"
- "Take a picture"
- "Stop the robot"

**Special Commands:**
- Type `quit` to exit
- Type `reset` to reset the robot

### Advanced Agent (Long-form Tasks)

For complex tasks with planning and memory:

```bash
python picarx_agent_advanced.py
```

**Special Commands:**
- Type `quit` to exit
- Type `reset` to reset the robot
- Type `status` to check task status
- Type `escape room` for a complex task example

### Programmatic Usage

Use the agent in your own scripts:

```python
from picarx_agent import PicarXAgent
from agents import Runner

# Initialize agent (uses API key from keys.py)
agent = PicarXAgent()

# Send commands
result = Runner.run_sync(agent.agent, "Drive forward at speed 30 for 2 seconds")
print(result.final_output)
```

### Example Scripts

Run the example scripts to see the agents in action:

```bash
# Basic agent examples
python example_agent_usage.py

# Advanced agent examples
python example_advanced_agent.py
```

## Example Commands

Here are some example commands you can try:

### Basic Movement
- "Drive forward at speed 30 for 2 seconds"
- "Turn left 15 degrees at speed 25"
- "Stop the robot"

### Sensor Reading
- "What's the distance from the ultrasonic sensor?"
- "Get the grayscale sensor readings"

### Camera Control
- "Turn the camera to look left"
- "Take a picture"
- "Point the camera down and take a photo"

### Complex Tasks
- "Drive forward slowly, then turn right and stop"
- "Look around with the camera and take a picture"
- "Check the distance, and if it's less than 10cm, stop"

### Safety
- "Reset all servos and stop the motors"
- "Emergency stop"

## Safety Features

- The agent includes safety instructions to be careful with movement commands
- All movement functions have speed limits (0-100)
- Servo angles are limited to safe ranges
- The `reset()` function provides a safe way to stop all operations

## Architecture

The agent uses the OpenAI Agents SDK with function calling:

1. **Agent Creation**: Creates an agent with tools corresponding to Picar-X functions using the `@tool` decorator
2. **Tool Execution**: Each tool is a Python function decorated with `@tool` that maps to Picar-X primitive functions
3. **Response Handling**: The SDK handles tool calling and provides natural language responses
4. **Built-in Tracing**: The SDK provides built-in tracing for debugging and monitoring

## Key Differences from Assistants API

This implementation uses the new OpenAI Agents SDK which provides:

- **Simpler API**: No need to manage threads, runs, or tool call handling manually
- **Built-in Tracing**: Automatic tracing for debugging and monitoring
- **Python-first**: Uses Python decorators and native language features
- **Automatic Schema Generation**: Tool schemas are generated automatically from function signatures
- **Better Error Handling**: More robust error handling and recovery

## Files

- `picarx_agent.py` - Main agent implementation using OpenAI Agents SDK
- `picarx_agent_advanced.py` - Advanced agent with memory and planning capabilities
- `picarx_primitives.py` - Hardware control functions
- `example_agent_usage.py` - Example usage script for basic agent
- `example_advanced_agent.py` - Example usage script for advanced agent
- `requirements.txt` - Python dependencies including `openai-agents`
- `keys.py` - API key configuration
- `AGENT_README.md` - This documentation

## Troubleshooting

### Common Issues

1. **API Key Not Found**
   ```
   Error: OPENAI_API_KEY not found in keys.py
   ```
   Solution: Add your OpenAI API key to `keys.py`

2. **Agents SDK Not Installed**
   ```
   ModuleNotFoundError: No module named 'agents'
   ```
   Solution: Install the OpenAI Agents SDK with `pip install openai-agents`

3. **Hardware Connection Issues**
   ```
   Error executing function: [hardware error]
   ```
   Solution: Check that your Picar-X is properly connected and powered

4. **Import Errors**
   ```
   ModuleNotFoundError: No module named 'picarx'
   ```
   Solution: Install the required dependencies with `pip install -r requirements.txt`

### Debug Mode

The OpenAI Agents SDK provides built-in tracing. You can enable it by setting:

```python
import os
os.environ["OPENAI_TRACING_V2_ENABLED"] = "true"
```

## Contributing

To add new functions to the agent:

1. Add the function to `picarx_primitives.py`
2. Create a new tool method in the agent class with the `@tool` decorator
3. Add the tool to the `tools` list in the agent initialization
4. Update the agent instructions if needed

Example:
```python
@tool
def new_function_tool(self, param: str) -> str:
    """Description of what this function does."""
    try:
        new_function(param)
        return f"Successfully executed {param}"
    except Exception as e:
        return f"Error: {str(e)}"
```

## License

This project is part of the Autonomous Benchmarking project and follows the same license terms. 