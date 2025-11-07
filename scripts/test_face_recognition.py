#!/usr/bin/env python3
"""
Test face recognition with camera
"""

import sys
sys.path.insert(0, '/home/tim/GairiHead')

from src.face_recognition_manager import FaceRecognitionManager
import cv2

def test_face_recognition():
    """Test face recognition system"""

    print("="*70)
    print("FACE RECOGNITION TEST")
    print("="*70)

    # Initialize manager
    print("\n📋 Initializing face recognition manager...")
    manager = FaceRecognitionManager()

    # Show what was loaded
    print(f"\n✅ Authorized users loaded: {list(manager.authorized_users.keys())}")
    for user, data in manager.authorized_users.items():
        num_encodings = len(data['encodings'])
        level = data['level']
        print(f"   - {user}: {num_encodings} face encodings, level {level}")

    if not manager.authorized_users:
        print("\n⚠️  No authorized users found!")
        print("   Make sure photos are in data/authorized_faces/{username}/")
        return False

    # Test with camera
    print(f"\n📸 Testing face recognition with camera...")
    print("   Position yourself in front of camera...")

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Could not open camera")
        return False

    # Capture a few frames to let camera adjust
    for _ in range(5):
        cap.read()

    # Capture test frame
    ret, frame = cap.read()
    cap.release()

    if not ret:
        print("❌ Could not capture frame from camera")
        return False

    print(f"   Frame captured: {frame.shape}")

    # Test recognition
    print("\n🔍 Running face recognition...")
    result = manager.recognize_face(frame)

    print("\n" + "="*70)
    print("RECOGNITION RESULT")
    print("="*70)

    if result:
        print(f"✅ Face recognized!")
        print(f"   User: {result.get('user', 'unknown')}")
        print(f"   Authorization Level: {result.get('level', 0)}")
        print(f"   Confidence: {result.get('confidence', 0):.2f}")

        level = result.get('level', 0)
        if level == 1:
            print(f"   Access: FULL (main user)")
        elif level == 2:
            print(f"   Access: LIMITED (guest)")
        elif level == 3:
            print(f"   Access: RESTRICTED (stranger)")

        print("="*70)
        return True
    else:
        print("⚠️  No face recognized")
        print("   This could mean:")
        print("   - No face detected in frame")
        print("   - Face not matched to any authorized user")
        print("   - Would be treated as Level 3 (stranger)")
        print("="*70)
        return False

if __name__ == "__main__":
    success = test_face_recognition()
    sys.exit(0 if success else 1)
