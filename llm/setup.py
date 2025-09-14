#!/usr/bin/env python3
"""
Setup script for LLM agent dependencies
"""

import subprocess
import sys
import os


def run_command(cmd):
    """Run a shell command and return success status."""
    try:
        result = subprocess.run(cmd, shell=True, check=True, 
                              capture_output=True, text=True)
        print(f"✓ {cmd}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {cmd}")
        print(f"Error: {e.stderr}")
        return False


def main():
    """Setup the Python environment."""
    print("Setting up LLM agent environment...")
    
    # Check Python version
    if sys.version_info < (3, 11):
        print("Error: Python 3.11 or higher is required")
        sys.exit(1)
    
    # Install dependencies
    commands = [
        "pip install -e .",
        "pip install openai pydantic pathspec tiktoken PyYAML python-dotenv aiohttp httpx"
    ]
    
    success = True
    for cmd in commands:
        if not run_command(cmd):
            success = False
    
    if success:
        print("\n✅ Setup complete!")
        print("You can now run: python main.py health-check")
    else:
        print("\n❌ Setup failed. Please check the errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()