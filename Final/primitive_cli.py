#!/usr/bin/env python3
"""
PicarX Primitives CLI Tool

This script allows you to run any primitive function from final_primitives.py
through a command-line interface. It provides help, lists all available functions,
and allows interactive execution of primitives.

Usage:
    python primitive_cli.py                    # Interactive mode
    python primitive_cli.py --list             # List all primitives
    python primitive_cli.py --help             # Show help
    python primitive_cli.py reset              # Run reset function
    python primitive_cli.py move_forward 50 2  # Run move_forward with args
"""

import sys
import inspect
import argparse
from typing import Any, Dict, List, Tuple
from final_primitives import *

class PrimitiveCLI:
    def __init__(self):
        self.primitives = self._get_primitives()
        self.excluded_functions = {'get_picarx'}  # Functions to exclude from CLI
        
    def _get_primitives(self) -> Dict[str, Dict]:
        """Extract all primitive functions and their signatures."""
        primitives = {}
        
        # Get all functions from final_primitives module
        for name, obj in inspect.getmembers(sys.modules['final_primitives']):
            if (inspect.isfunction(obj) and 
                not name.startswith('_') and 
                name not in self.excluded_functions):
                
                # Get function signature
                sig = inspect.signature(obj)
                params = []
                
                for param_name, param in sig.parameters.items():
                    param_info = {
                        'name': param_name,
                        'type': param.annotation if param.annotation != inspect.Parameter.empty else 'Any',
                        'default': param.default if param.default != inspect.Parameter.empty else None,
                        'required': param.default == inspect.Parameter.empty
                    }
                    params.append(param_info)
                
                primitives[name] = {
                    'function': obj,
                    'docstring': obj.__doc__ or "No documentation available",
                    'parameters': params,
                    'return_type': sig.return_annotation if sig.return_annotation != inspect.Parameter.empty else 'Any'
                }
        
        return primitives
    
    def list_primitives(self):
        """List all available primitives with their signatures."""
        print("=" * 80)
        print("AVAILABLE PICARX PRIMITIVES")
        print("=" * 80)
        
        for name, info in sorted(self.primitives.items()):
            print(f"\n🔧 {name}")
            print(f"   {info['docstring']}")
            
            if info['parameters']:
                print("   Parameters:")
                for param in info['parameters']:
                    required = " (required)" if param['required'] else f" (default: {param['default']})"
                    print(f"     - {param['name']}: {param['type']}{required}")
            else:
                print("   Parameters: None")
            
            print(f"   Returns: {info['return_type']}")
            print("-" * 80)
    
    def show_help(self):
        """Show detailed help information."""
        print("=" * 80)
        print("PICARX PRIMITIVES CLI HELP")
        print("=" * 80)
        print("""
This tool allows you to run any primitive function from final_primitives.py

USAGE:
    python primitive_cli.py [OPTIONS] [FUNCTION] [ARGUMENTS...]

OPTIONS:
    --list, -l          List all available primitives
    --help, -h          Show this help message
    --interactive, -i   Start interactive mode (default if no function specified)

EXAMPLES:
    # List all primitives
    python primitive_cli.py --list
    
    # Run a function with no parameters
    python primitive_cli.py reset
    
    # Run a function with parameters
    python primitive_cli.py move_forward 50 2.5
    python primitive_cli.py set_dir_servo -15
    python primitive_cli.py turn_left 30 40 1.0
    
    # Interactive mode
    python primitive_cli.py
    python primitive_cli.py --interactive

INTERACTIVE MODE:
    In interactive mode, you can:
    - Type 'list' to see all primitives
    - Type 'help <function>' to see help for a specific function
    - Type 'run <function> [args...]' to run a function
    - Type 'quit' or 'exit' to exit
    
    Example interactive session:
    > list
    > help move_forward
    > run move_forward 30 2.0
    > quit
        """)
    
    def show_function_help(self, function_name: str):
        """Show detailed help for a specific function."""
        if function_name not in self.primitives:
            print(f"❌ Function '{function_name}' not found!")
            print("Use 'list' to see all available functions.")
            return
        
        info = self.primitives[function_name]
        print(f"\n🔧 {function_name}")
        print("=" * 50)
        print(f"Description: {info['docstring']}")
        print(f"Returns: {info['return_type']}")
        
        if info['parameters']:
            print("\nParameters:")
            for param in info['parameters']:
                required = " (REQUIRED)" if param['required'] else f" (default: {param['default']})"
                print(f"  • {param['name']}: {param['type']}{required}")
        else:
            print("\nParameters: None")
        
        print(f"\nUsage: {function_name}({', '.join([p['name'] for p in info['parameters']])})")
    
    def parse_arguments(self, args: List[str]) -> Tuple[Any, ...]:
        """Parse command line arguments for a function."""
        if not args:
            return ()
        
        parsed_args = []
        for i, arg in enumerate(args):
            try:
                # Try to convert to int first
                parsed_args.append(int(arg))
            except ValueError:
                try:
                    # Try to convert to float
                    parsed_args.append(float(arg))
                except ValueError:
                    # Keep as string
                    parsed_args.append(arg)
        
        return tuple(parsed_args)
    
    def run_function(self, function_name: str, args: List[str]) -> Any:
        """Run a primitive function with the given arguments."""
        if function_name not in self.primitives:
            print(f"❌ Function '{function_name}' not found!")
            print("Use 'list' to see all available functions.")
            return None
        
        info = self.primitives[function_name]
        function = info['function']
        
        try:
            # Parse arguments
            parsed_args = self.parse_arguments(args)
            
            # Check if we have the right number of arguments
            required_params = [p for p in info['parameters'] if p['required']]
            if len(parsed_args) < len(required_params):
                print(f"❌ Not enough arguments! Function requires {len(required_params)} arguments.")
                print(f"Required: {[p['name'] for p in required_params]}")
                return None
            
            if len(parsed_args) > len(info['parameters']):
                print(f"❌ Too many arguments! Function accepts {len(info['parameters'])} arguments.")
                print(f"Parameters: {[p['name'] for p in info['parameters']]}")
                return None
            
            # Run the function
            print(f"🚀 Running {function_name}({', '.join(map(str, parsed_args))})...")
            result = function(*parsed_args)
            
            if result is not None:
                print(f"✅ Result: {result}")
            else:
                print("✅ Function completed successfully")
            
            return result
            
        except Exception as e:
            print(f"❌ Error running {function_name}: {str(e)}")
            return None
    
    def interactive_mode(self):
        """Start interactive mode."""
        print("=" * 80)
        print("PICARX PRIMITIVES INTERACTIVE MODE")
        print("=" * 80)
        print("Type 'help' for commands, 'quit' to exit")
        print()
        
        while True:
            try:
                command = input("picarx> ").strip().split()
                
                if not command:
                    continue
                
                cmd = command[0].lower()
                
                if cmd in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break
                
                elif cmd == 'list':
                    self.list_primitives()
                
                elif cmd == 'help':
                    if len(command) > 1:
                        self.show_function_help(command[1])
                    else:
                        self.show_help()
                
                elif cmd == 'run':
                    if len(command) < 2:
                        print("❌ Usage: run <function> [args...]")
                        continue
                    self.run_function(command[1], command[2:])
                
                elif cmd in self.primitives:
                    # Direct function call
                    self.run_function(cmd, command[1:])
                
                else:
                    print(f"❌ Unknown command: {cmd}")
                    print("Type 'help' for available commands")
            
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except EOFError:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {str(e)}")

def main():
    cli = PrimitiveCLI()
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="PicarX Primitives CLI Tool",
        add_help=False
    )
    parser.add_argument('--list', '-l', action='store_true', help='List all primitives')
    parser.add_argument('--help', '-h', action='store_true', help='Show help')
    parser.add_argument('--interactive', '-i', action='store_true', help='Start interactive mode')
    parser.add_argument('function', nargs='?', help='Function to run')
    parser.add_argument('args', nargs='*', help='Function arguments')
    
    args, unknown = parser.parse_known_args()
    
    # Handle help
    if args.help or (not args.function and not args.list and not args.interactive):
        cli.show_help()
        return
    
    # Handle list
    if args.list:
        cli.list_primitives()
        return
    
    # Handle function execution
    if args.function:
        cli.run_function(args.function, args.args)
        return
    
    # Default to interactive mode
    cli.interactive_mode()

if __name__ == "__main__":
    main()
