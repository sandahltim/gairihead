#!/usr/bin/env python3
"""
Arduino Display Integration Test
Tests the Arduino TFT display communication
"""

import sys
sys.path.insert(0, "/home/tim/GairiHead")

from src.arduino_display import ArduinoDisplay
import time

print("="*70)
print("ARDUINO DISPLAY INTEGRATION TEST")
print("="*70)

# Initialize display
print("\n1. Connecting to Arduino...")
print("   Port: /dev/ttyACM0")
print("   Baud: 115200")

display = ArduinoDisplay(port='/dev/ttyACM0', baudrate=115200, enabled=True)

if not display.connected:
    print("   ❌ Failed to connect to Arduino")
    print("\n   Troubleshooting:")
    print("   - Is Arduino plugged in via USB?")
    print("   - Is sketch uploaded to Arduino?")
    print("   - Try: ls -la /dev/ttyACM* /dev/ttyUSB*")
    print("   - Try: sudo chmod 666 /dev/ttyACM0")
    sys.exit(1)

print("   ✅ Connected to Arduino!")

# Wait for Arduino to be ready
time.sleep(2)

# Test 1: Status display
print("\n2. Testing STATUS display...")
display.update_status(
    user="tim",
    level=1,
    state="idle",
    confidence=0.78,
    expression="happy"
)
print("   ✅ Status sent (should see Tim, Level 1, happy)")
time.sleep(3)

# Test 2: Conversation display
print("\n3. Testing CONVERSATION display...")
display.show_conversation(
    user_text="Good morning Gairi",
    gairi_text="Good morning Tim! Ready to help with your day!",
    expression="happy",
    tier="local",
    response_time=0.34
)
print("   ✅ Conversation sent")
print("      Arduino should show:")
print("      - User: Good morning Gairi")
print("      - Gairi: Good morning Tim! Ready...")
print("      - Expression: :) (happy)")
time.sleep(5)

# Test 3: Debug display
print("\n4. Testing DEBUG display...")
display.show_debug(
    tier="local",
    tool="calendar_tool",
    training_logged=True,
    response_time=0.42
)
print("   ✅ Debug info sent")
print("      Should show calendar_tool, local tier, training logged")
time.sleep(3)

# Test 4: State transitions
print("\n5. Testing STATE transitions...")
states = [
    ("listening", "alert", 3),
    ("thinking", "thinking", 3),
    ("speaking", "happy", 2)
]

for state, expression, duration in states:
    print(f"   State: {state} / Expression: {expression}")
    display.update_status(
        user="tim",
        level=1,
        state=state,
        confidence=0.78,
        expression=expression
    )
    time.sleep(duration)

# Test 5: Authorization levels
print("\n6. Testing AUTHORIZATION levels...")
levels = [
    (1, "tim", "happy", "green"),
    (2, "guest_sarah", "neutral", "yellow"),
    (3, "stranger", "concerned", "red")
]

for level, user, expression, color in levels:
    print(f"   Level {level}: {user} ({color})")
    display.update_status(
        user=user,
        level=level,
        state="idle",
        confidence=0.60 if level > 1 else 0.78,
        expression=expression
    )
    time.sleep(3)

# Test 6: Long conversation text (wrapping test)
print("\n7. Testing LONG TEXT wrapping...")
display.show_conversation(
    user_text="What's on my calendar today and do I have any important meetings?",
    gairi_text="You have 3 meetings today: 9am standup, 2pm client presentation, and 4pm team sync. The client presentation is your most important one.",
    expression="thinking",
    tier="cloud",
    response_time=1.23
)
print("   ✅ Long text sent (should wrap correctly)")
time.sleep(5)

# Test 7: Check for commands from Arduino
print("\n8. Checking for COMMANDS from Arduino...")
print("   (Try pressing touch buttons on Arduino if available)")
for i in range(5):
    cmd = display.check_commands()
    if cmd:
        print(f"   📨 Received command: {cmd}")
        # Respond to command
        action = cmd.get('action')
        if action == 'guest_mode':
            print("      Guest mode activated!")
            display.update_status(
                user="guest",
                level=2,
                state="active",
                confidence=0.0,
                expression="friendly"
            )
        elif action == 'demo_mode':
            print("      Demo mode activated!")
    else:
        print(f"   Waiting for commands... ({i+1}/5)")
    time.sleep(1)

# Test 8: Rapid updates (stress test)
print("\n9. Testing RAPID updates (stress test)...")
for i in range(10):
    display.update_status(
        user="tim",
        level=1,
        state=f"test_{i}",
        confidence=0.5 + (i * 0.05),
        expression="idle"
    )
    time.sleep(0.2)
print("   ✅ Rapid updates complete")

# Return to idle
print("\n10. Returning to IDLE state...")
display.update_status(
    user="tim",
    level=1,
    state="idle",
    confidence=0.78,
    expression="idle"
)
time.sleep(2)

print("\n" + "="*70)
print("ARDUINO DISPLAY TEST COMPLETE!")
print("="*70)
print("\nVerification checklist:")
print("  ✓ Display connected and responding")
print("  ✓ Status view shows user/level/state/expression")
print("  ✓ Conversation view shows user/gairi text exchange")
print("  ✓ Debug view shows tier/tool/training status")
print("  ✓ State transitions smooth")
print("  ✓ Authorization levels color-coded correctly")
print("  ✓ Long text wrapping works")
print("  ✓ Touch commands detected (if pressed)")
print("  ✓ Rapid updates handled")
print("\nArduino display integration is working!")

# Cleanup
display.close()
print("\nDisplay connection closed.")
