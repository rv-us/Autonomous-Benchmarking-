# OpenAI Agents SDK Memory & Multiturn Conversations

## Overview

The OpenAI Agents SDK (version 0.2.x) provides built-in memory and session management capabilities that are fully compatible with Python 3.9+ and Raspberry Pi environments. This makes it perfect for the Picar-X robot project.

## Key Components

### 1. Session Management

```python
from agents import SQLiteSession, Runner

# Create a persistent session
session = SQLiteSession(
    session_id="my_robot_session",
    db_path="robot_memory.db"  # File path for persistence
)

# Use in-memory session (lost when process ends)
session = SQLiteSession(session_id="temp_session")  # Uses :memory: by default
```

### 2. Multiturn Conversations

```python
from agents import Agent, Runner

# Create agent
agent = Agent(name="Robot", instructions="...", tools=[...])

# Run with session for memory
result = Runner.run_sync(
    agent, 
    "Remember that the kitchen is to my left",
    session=session
)

# Later conversation - agent remembers previous context
result = Runner.run_sync(
    agent,
    "Where is the kitchen?",
    session=session  # Same session = remembers previous conversation
)
```

## Memory Capabilities

### Automatic Context Retention
- **Conversation History**: All messages and responses are automatically stored
- **Tool Calls**: Function calls and their results are remembered
- **Context Building**: Agents can reference previous interactions naturally

### Persistent Storage
- **SQLite Backend**: Uses SQLite database for reliable storage
- **File-based**: Survives process restarts and system reboots
- **Session Isolation**: Different session IDs create separate memory contexts

### Cross-Instance Memory
- **Shared Sessions**: Multiple agent instances can share the same session
- **Process Independence**: Memory persists even if the Python process restarts
- **Concurrent Access**: Multiple processes can access the same session safely

## Implementation Patterns for Picar-X

### 1. Basic Memory Setup

```python
from agents import Agent, Runner, SQLiteSession
from picarx_primitives import *

class MemoryRobot:
    def __init__(self, session_id="picarx_main"):
        self.session = SQLiteSession(
            session_id=session_id,
            db_path="/home/pi/picarx_memory.db"  # Persistent on Pi
        )
        
        self.agent = Agent(
            name="Picar-X with Memory",
            instructions="You remember all our previous conversations...",
            tools=[drive_forward_tool, get_ultrasound_tool, ...]
        )
    
    def chat(self, message):
        return Runner.run_sync(self.agent, message, session=self.session)
```

### 2. Task Continuity

```python
# Session 1: Start a task
robot = MemoryRobot("exploration_session")
robot.chat("Start mapping the room. Take a picture here as reference point A.")

# Session 2: Continue later (even after restart)
robot = MemoryRobot("exploration_session")  # Same session_id
robot.chat("Continue the room mapping from where we left off.")
# Agent remembers reference point A and continues the task
```

### 3. Location Memory

```python
@function_tool
def remember_location_tool(name: str, description: str) -> str:
    """Remember a location with name and description."""
    return f"Remembered location '{name}': {description}"

# Usage
robot.chat("Remember this spot as 'charging_station' - it's next to the wall outlet")
# Later...
robot.chat("Navigate back to the charging station")
# Agent remembers the location and can reference it
```

### 4. Sensor History

```python
@function_tool
def log_sensor_reading_tool(sensor_type: str, value: float, location: str) -> str:
    """Log a sensor reading with context."""
    return f"Logged {sensor_type} reading: {value} at {location}"

# Build sensor history over time
robot.chat("Check ultrasonic sensor and log the reading at 'living_room_center'")
robot.chat("Drive to the kitchen and log another ultrasonic reading")
robot.chat("Compare the sensor readings between living room and kitchen")
```

## Advanced Features

### 1. Multiple Sessions for Different Contexts

```python
# Different sessions for different rooms/tasks
kitchen_robot = MemoryRobot("kitchen_exploration")
bedroom_robot = MemoryRobot("bedroom_exploration")
security_robot = MemoryRobot("security_patrol")

# Each maintains separate memory and context
```

### 2. Session Management Tools

```python
@function_tool
def switch_session_tool(new_session_id: str) -> str:
    """Switch to a different memory session."""
    # Implementation would recreate the session
    return f"Switched to session: {new_session_id}"

@function_tool
def list_sessions_tool() -> str:
    """List available memory sessions."""
    # Implementation would query the database
    return "Available sessions: kitchen, bedroom, security"
```

### 3. Memory Analysis

```python
@function_tool
def analyze_memory_tool(topic: str) -> str:
    """Analyze memory for patterns related to a topic."""
    return f"Analyzing memory for patterns related to: {topic}"

# Usage
robot.chat("Analyze my memory for patterns about obstacle locations")
robot.chat("What have I learned about the best paths through the house?")
```

## Python 3.9 Compatibility

The OpenAI Agents SDK version 0.2.x is fully compatible with Python 3.9:

### Requirements
```txt
openai-agents>=0.2.0
openai>=1.0.0
sqlite3  # Built into Python 3.9+
```

### Raspberry Pi Considerations
- **Storage**: Use SD card path for persistent storage: `/home/pi/robot_memory.db`
- **Performance**: SQLite is lightweight and efficient on Pi hardware
- **Reliability**: Database survives power cycles and system restarts

## Best Practices

### 1. Session Naming
```python
# Use descriptive session names
session_id = f"picarx_{task_type}_{date}"  # e.g., "picarx_exploration_2024_01_15"
```

### 2. Memory Management
```python
# Periodic cleanup for long-running sessions
@function_tool
def cleanup_old_memory_tool(days_old: int = 30) -> str:
    """Clean up memory older than specified days."""
    # Implementation would clean old entries
    return f"Cleaned memory older than {days_old} days"
```

### 3. Error Handling
```python
def safe_chat(self, message):
    try:
        return Runner.run_sync(self.agent, message, session=self.session)
    except Exception as e:
        # Fallback to no-memory mode if session fails
        return Runner.run_sync(self.agent, message)
```

### 4. Backup and Recovery
```python
import shutil
from datetime import datetime

def backup_memory(db_path="/home/pi/picarx_memory.db"):
    """Backup the memory database."""
    backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(db_path, backup_path)
    return backup_path
```

## Example Use Cases

### 1. Home Security Patrol
- Remember patrol routes and timing
- Log unusual sensor readings with locations
- Build patterns of normal vs. abnormal activity

### 2. Room Mapping and Navigation
- Remember room layouts and obstacle locations
- Build optimal path knowledge over time
- Reference landmarks and waypoints

### 3. Interactive Pet/Companion
- Remember user preferences and interactions
- Build personality based on conversation history
- Maintain long-term relationships and context

### 4. Research and Data Collection
- Log sensor data with timestamps and locations
- Build environmental models over time
- Remember experimental procedures and results

## Troubleshooting

### Common Issues
1. **Database Lock**: Multiple processes accessing same session
   - Solution: Use different session IDs or implement proper locking

2. **Memory Growth**: Long-running sessions accumulating data
   - Solution: Implement periodic cleanup or session rotation

3. **Storage Space**: Large conversation histories on Pi
   - Solution: Regular backups and cleanup of old sessions

### Debug Mode
```python
import os
os.environ["OPENAI_TRACING_V2_ENABLED"] = "true"  # Enable detailed tracing
```

This comprehensive memory system makes the Picar-X robot much more capable of complex, long-term tasks and natural interactions!