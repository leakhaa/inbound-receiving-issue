#!/usr/bin/env python3
"""
Test script to demonstrate live printing functionality
"""
import time
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import broadcast_print_output

def test_live_printing():
    """Test the live printing functionality"""
    print("Starting live printing test...")
    
    # Simulate some backend processing with live updates
    for i in range(5):
        message = f"Processing step {i+1}/5..."
        print(f"🔍 {message}")
        broadcast_print_output(f"🔍 {message}")
        time.sleep(1)
    
    print("✅ Live printing test completed!")
    broadcast_print_output("✅ Live printing test completed!")

if __name__ == "__main__":
    test_live_printing()
