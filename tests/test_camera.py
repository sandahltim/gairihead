#!/usr/bin/env python3
"""
Test camera_manager.py with USB or Pi Camera Module
Run from GairiHead directory: python tests/test_camera.py
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from camera_manager import test_camera, test_face_detection
from loguru import logger


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("GairiHead Camera Test")
    logger.info("=" * 60)

    print("\nChoose test:")
    print("1. Basic camera test (30 frames)")
    print("2. Face detection test (live)")
    print("3. Both")

    choice = input("\nEnter choice (1/2/3): ").strip()

    try:
        if choice == "1":
            test_camera()
        elif choice == "2":
            test_face_detection()
        elif choice == "3":
            test_camera()
            print("\n" + "=" * 60)
            print("Starting face detection test in 2 seconds...")
            import time
            time.sleep(2)
            test_face_detection()
        else:
            print("Invalid choice")
            sys.exit(1)

    except KeyboardInterrupt:
        logger.info("\nTest interrupted by user")
    except Exception as e:
        logger.error(f"Test failed: {e}")
        sys.exit(1)
