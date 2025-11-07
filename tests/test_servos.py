#!/usr/bin/env python3
"""
Test servos - verify all 3 servos work correctly

Run this first before anything else!
"""

import sys
sys.path.insert(0, '/Gary/GairiHead/src')

from servo_controller import test_servos

if __name__ == "__main__":
    print("=" * 60)
    print("GairiHead Servo Test")
    print("=" * 60)
    print()
    print("This will test all 3 servos:")
    print("  - Left eyelid (GPIO 17)")
    print("  - Right eyelid (GPIO 27)")
    print("  - Mouth (GPIO 22)")
    print()
    print("Press Ctrl+C to stop")
    print("=" * 60)
    print()

    test_servos()
