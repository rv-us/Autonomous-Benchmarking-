"""
example_memory_usage.py

Example demonstrating advanced memory and multiturn conversation patterns
with the Picar-X robot using openai-agents SDK.
"""

from picarx_agent_with_memory import PicarXAgentWithMemory
import time

def demo_basic_memory():
    """Demonstrate basic memory functionality."""
    print("=== Basic Memory Demo ===")
    
    agent = PicarXAgentWithMemory(session_id="memory_demo")
    
    # First conversation - establish context
    print("Setting up initial context...")
    response1 = agent.chat("My name is Alex and I'm testing the robot in my living room.")
    print(f"Agent: {response1}")
    
    # Second conversation - reference previous context
    print("\nReferencing previous context...")
    response2 = agent.chat("What's my name and where am I testing you?")
    print(f"Agent: {response2}")
    
    # Third conversation - build on context
    print("\nBuilding on context...")
    response3 = agent.chat("Drive forward 2 seconds and remember this as the 'start position'")
    print(f"Agent: {response3}")
    
    return agent

def demo_task_continuity():
    """Demonstrate task continuity across multiple interactions."""
    print("\n=== Task Continuity Demo ===")
    
    agent = PicarXAgentWithMemory(session_id="task_demo")
    
    # Set a long-term goal
    response1 = agent.chat("Set a goal to map out my room by taking pictures at different locations")
    print(f"Agent: {response1}")
    
    # Continue the task in subsequent interactions
    response2 = agent.chat("Let's start the room mapping. Take a picture here first.")
    print(f"Agent: {response2}")
    
    # Simulate time passing, then continue
    print("\n[Simulating time passing...]")
    response3 = agent.chat("Now drive forward and take another picture for the room map")
    print(f"Agent: {response3}")
    
    # Check progress on the goal
    response4 = agent.chat("How is our room mapping goal progressing?")
    print(f"Agent: {response4}")
    
    return agent

def demo_sensor_memory():
    """Demonstrate remembering sensor readings over time."""
    print("\n=== Sensor Memory Demo ===")
    
    agent = PicarXAgentWithMemory(session_id="sensor_demo")
    
    # Take initial sensor readings
    response1 = agent.chat("Check the ultrasonic sensor and remember this as the baseline distance")
    print(f"Agent: {response1}")
    
    # Move and compare
    response2 = agent.chat("Drive forward 1 second, then check the sensor again. How does it compare to the baseline?")
    print(f"Agent: {response2}")
    
    # Ask for analysis
    response3 = agent.chat("Based on the sensor readings you've taken, what can you tell me about the environment?")
    print(f"Agent: {response3}")
    
    return agent

def demo_session_persistence():
    """Demonstrate that memory persists across different agent instances."""
    print("\n=== Session Persistence Demo ===")
    
    # Create first agent instance
    agent1 = PicarXAgentWithMemory(session_id="persistence_test")
    response1 = agent1.chat("Remember that the red chair is to my left and the table is straight ahead")
    print(f"Agent 1: {response1}")
    
    # Create second agent instance with same session ID
    print("\n[Creating new agent instance with same session...]")
    agent2 = PicarXAgentWithMemory(session_id="persistence_test")
    response2 = agent2.chat("Where is the red chair located?")
    print(f"Agent 2: {response2}")
    
    return agent2

def demo_multiple_sessions():
    """Demonstrate managing multiple separate sessions."""
    print("\n=== Multiple Sessions Demo ===")
    
    # Session 1 - Kitchen exploration
    kitchen_agent = PicarXAgentWithMemory(session_id="kitchen_session")
    response1 = kitchen_agent.chat("I'm in the kitchen. Remember that the fridge is behind me.")
    print(f"Kitchen Agent: {response1}")
    
    # Session 2 - Living room exploration  
    living_agent = PicarXAgentWithMemory(session_id="living_room_session")
    response2 = living_agent.chat("I'm in the living room. The TV is in front of me.")
    print(f"Living Room Agent: {response2}")
    
    # Test session isolation
    response3 = kitchen_agent.chat("Where is the TV?")
    print(f"Kitchen Agent (shouldn't know about TV): {response3}")
    
    response4 = living_agent.chat("Where is the fridge?")
    print(f"Living Room Agent (shouldn't know about fridge): {response4}")

def main():
    """Run all memory demonstration examples."""
    print("OpenAI Agents SDK Memory & Multiturn Conversation Demo")
    print("=" * 60)
    
    try:
        # Run all demos
        demo_basic_memory()
        demo_task_continuity()
        demo_sensor_memory()
        demo_session_persistence()
        demo_multiple_sessions()
        
        print("\n" + "=" * 60)
        print("All memory demos completed!")
        print("\nKey takeaways:")
        print("- Sessions automatically maintain conversation history")
        print("- Memory persists across agent instances with same session_id")
        print("- Different session_ids create isolated conversation contexts")
        print("- Agents can reference previous interactions and build context")
        print("- Perfect for long-term robot tasks and exploration")
        
    except Exception as e:
        print(f"Demo error: {str(e)}")

if __name__ == "__main__":
    main()