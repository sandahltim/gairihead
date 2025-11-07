#!/usr/bin/env python3
"""
Monitor Arduino touch screen debug output
"""

import serial
import time

print("="*70)
print("ARDUINO TOUCH MONITOR")
print("="*70)
print("\nConnecting to Arduino...")

ser = serial.Serial('/dev/ttyACM0', 115200, timeout=0.5)
time.sleep(3)  # Wait for Arduino reset

print("✅ Connected! Touch the screen to see debug output.\n")
print("Touch events will appear below:")
print("-" * 70)

try:
    while True:
        if ser.in_waiting:
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            if line and ('TOUCH' in line or 'BTN' in line or 'MAPPED' in line):
                print(line)
        time.sleep(0.01)

except KeyboardInterrupt:
    print("\n\n" + "="*70)
    print("Monitoring stopped")
    print("="*70)
    ser.close()
