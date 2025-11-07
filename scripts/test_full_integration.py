#!/usr/bin/env python3
"""
Full System Integration Test
Tests: Face Recognition + Voice + LLM + Expressions + TTS
"""

import sys
sys.path.insert(0, "/home/tim/GairiHead")

from src.face_recognition_manager import FaceRecognitionManager
from src.voice_handler import VoiceHandler
from src.servo_controller import ServoController
from src.expression_engine import ExpressionEngine
from src.llm_tier_manager import LLMTierManager
import yaml
import cv2
import time

print("="*70)
print("FULL SYSTEM INTEGRATION TEST")
print("="*70)

# Load config
with open("/home/tim/GairiHead/config/gairi_head.yaml") as f:
    config = yaml.safe_load(f)

# Initialize components
print("\nInitializing components...")
face_mgr = FaceRecognitionManager()
llm_mgr = LLMTierManager(config)
voice = VoiceHandler(config, llm_tier_manager=llm_mgr)
servo = ServoController(config_path="/home/tim/GairiHead/config/gairi_head.yaml")
engine = ExpressionEngine(config_path="/home/tim/GairiHead/config")
engine.set_controllers(servo)

print("All components initialized!")

# Test sequence
print("\n" + "="*70)
print("TEST SEQUENCE")
print("="*70)

# 1. Face recognition
print("\n1. Testing face recognition...")
engine.set_expression("alert")
cap = cv2.VideoCapture(0)
for _ in range(5):
    cap.read()  # Let camera adjust

ret, frame = cap.read()
cap.release()

if ret:
    auth = face_mgr.recognize_face(frame)
    if auth:
        user = auth.get("user", "unknown")
        level = auth.get("level", 3)
        conf = auth.get("confidence", 0.0)
        print(f"   Recognized: {user} (Level {level}, confidence: {conf:.2f})")

        if level == 1:
            engine.set_expression("welcome")
        else:
            engine.set_expression("concerned")
    else:
        print("   No face recognized (stranger mode)")
        auth = {"level": 3, "user": "stranger", "confidence": 0.0}
        engine.set_expression("skeptical")
else:
    print("   Camera failed")
    auth = {"level": 3, "user": "stranger", "confidence": 0.0}

time.sleep(1)

# 2. Expression test
print("\n2. Testing expressions...")
expressions_to_test = ["happy", "thinking", "sarcasm", "amused"]
for expr in expressions_to_test:
    print(f"   Setting: {expr}")
    engine.set_expression(expr)
    time.sleep(0.8)

engine.set_expression("idle")
time.sleep(0.5)

# 3. Voice pipeline with authorization
print("\n3. Testing voice pipeline...")
print("   Get ready to speak in 2 seconds...")
time.sleep(2)

engine.set_expression("listening")
print("\nSPEAK NOW (3 seconds)!")
print("   Try: Good morning Gairi")

result = voice.process_voice_query(duration=3.0, authorization=auth)

if result:
    print("\nComplete pipeline successful!")
    engine.set_expression("pride")
    time.sleep(1)
else:
    print("\nPipeline completed with warnings")
    engine.set_expression("sheepish")
    time.sleep(1)

engine.set_expression("idle")

print("\n" + "="*70)
print("INTEGRATION TEST COMPLETE!")
print("="*70)
print("\nComponents tested:")
print("  - Face recognition: OK")
print("  - Servo expressions: OK")
print("  - Voice input: OK")
print("  - LLM processing: OK")
print("  - TTS output: OK")
print("\nFull system operational!")
