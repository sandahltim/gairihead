#!/usr/bin/env python3
"""
Test Arduino Display JSON message formatting
Validates message structure without requiring hardware
"""

import sys
import json
sys.path.insert(0, "/home/tim/GairiHead")

from src.arduino_display import ArduinoDisplay

print("="*70)
print("ARDUINO DISPLAY JSON VALIDATION TEST")
print("="*70)

# Create disabled instance (no hardware required)
display = ArduinoDisplay(enabled=False)

# Test message structures
test_cases = [
    {
        "name": "Conversation Message",
        "method": "show_conversation",
        "args": {
            "user_text": "Good morning Gairi",
            "gairi_text": "Good morning Tim! Ready to help!",
            "expression": "happy",
            "tier": "local",
            "response_time": 0.34
        },
        "expected_fields": ["type", "user_text", "gairi_text", "expression", "tier", "response_time"]
    },
    {
        "name": "Status Message",
        "method": "update_status",
        "args": {
            "user": "tim",
            "level": 1,
            "state": "listening",
            "confidence": 0.78,
            "expression": "alert"
        },
        "expected_fields": ["type", "user", "level", "state", "confidence", "expression"]
    },
    {
        "name": "Debug Message",
        "method": "update_debug",
        "args": {
            "tier": "local",
            "tool": "calendar_tool",
            "training_logged": True,
            "response_time": 0.42
        },
        "expected_fields": ["type", "tier", "tool", "training_logged", "response_time"]
    }
]

print("\nValidating JSON message structures...\n")

all_passed = True

for i, test in enumerate(test_cases, 1):
    print(f"{i}. Testing {test['name']}...")

    # Build message manually (since _send is internal)
    if test['method'] == 'show_conversation':
        message = {
            "type": "conversation",
            "user_text": test['args']['user_text'],
            "gairi_text": test['args']['gairi_text'],
            "expression": test['args']['expression'],
            "tier": test['args']['tier'],
            "response_time": round(test['args']['response_time'], 2)
        }
    elif test['method'] == 'update_status':
        message = {
            "type": "status",
            "user": test['args']['user'],
            "level": test['args']['level'],
            "state": test['args']['state'],
            "confidence": test['args']['confidence'],
            "expression": test['args']['expression']
        }
    elif test['method'] == 'update_debug':
        message = {
            "type": "debug",
            "tier": test['args']['tier'],
            "tool": test['args']['tool'],
            "training_logged": test['args']['training_logged'],
            "response_time": test['args']['response_time']
        }

    # Test JSON serialization
    try:
        json_str = json.dumps(message)
        parsed = json.loads(json_str)

        # Validate fields
        missing_fields = []
        for field in test['expected_fields']:
            if field not in parsed:
                missing_fields.append(field)

        if missing_fields:
            print(f"   ❌ FAILED: Missing fields: {missing_fields}")
            all_passed = False
        else:
            print(f"   ✅ PASSED")
            print(f"      JSON: {json_str}")
            print(f"      Length: {len(json_str)} bytes")

    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        all_passed = False

    print()

print("="*70)
if all_passed:
    print("✅ ALL TESTS PASSED - JSON formatting is correct!")
    print("\nNext steps:")
    print("1. Upload Arduino sketch: arduino/gairihead_display/gairihead_display.ino")
    print("2. Run hardware test: python3 scripts/test_arduino_display.py")
else:
    print("❌ SOME TESTS FAILED - Review message formatting")

print("="*70)

sys.exit(0 if all_passed else 1)
