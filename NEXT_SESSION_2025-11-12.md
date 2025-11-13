# Next Session Quick Start - 2025-11-12

**Previous Session**: Pico NeoPixel eyes wired and tested
**Next Focus**: UART communication testing and system integration

---

## Current Status ✓

**Hardware:**
- ✓ Pico W connected via USB to Pi 5
- ✓ Left eye NeoPixel on GP2 (working)
- ✓ Right eye NeoPixel on GP3 (working)
- ✓ UART wired: GP0→Pin 10, GP1→Pin 8
- ✓ Power: 5V external supply for NeoPixels
- ✓ Eyes showing blue pulse (idle mode)

**Software:**
- ✓ CircuitPython 9.2.1 installed on Pico
- ✓ NeoPixel controller code loaded
- ✓ UART enabled on Pi 5
- ✓ Test script ready

---

## Start Here - UART Communication Test

### Step 1: Verify Wiring

Check these 2 UART connections:
```
Pico GP0 (Pin 1) ──→ Pi 5 Pin 10 (GPIO 15)
Pico GP1 (Pin 2) ←── Pi 5 Pin 8  (GPIO 14)
```

**CRITICAL**: TX crosses to RX!

### Step 2: Run Test

```bash
cd ~/GairiHead
python3 tests/test_pico_uart.py
```

**Expected**: Eyes cycle through all expressions and colors (2-3 minutes)

### Step 3: If Test Fails

**No response from Pico:**
```bash
# Check UART device
ls -l /dev/serial0

# Check Pico USB connection
ls -l /dev/ttyACM0

# Monitor Pico debug output
python3 -c "
import serial
ser = serial.Serial('/dev/ttyACM0', 115200)
while True:
    if ser.in_waiting:
        print(ser.readline().decode())
"
```

**TX/RX swapped?**
- Swap GP0 and GP1 connections
- Re-run test

**Garbled data?**
- Check baud rate (should be 115200)
- Check common ground

---

## After UART Test Passes

### Task 1: Create Pico Controller Module

```bash
# Create wrapper for UART commands
nano src/pico_controller.py
```

Basic structure:
```python
import serial

class PicoController:
    def __init__(self, port='/dev/serial0', baud=115200):
        self.ser = serial.Serial(port, baud, timeout=1)

    def send_expression(self, name):
        # Send EXPR:name command
        pass

    def set_color(self, r, g, b):
        # Send COLOR:r,g,b command
        pass
```

### Task 2: Integrate with Hardware Coordinator

```bash
nano src/hardware_coordinator.py
```

Add PicoController to existing servo/camera coordination.

### Task 3: Test Combined Expressions

```bash
python3 tests/test_full_expressions.py  # To be created
```

---

## Quick Commands

```bash
# Test single UART command
python3 -c "
import serial, time
ser = serial.Serial('/dev/serial0', 115200, timeout=1)
time.sleep(1)
ser.write(b'EXPR:happy\n')
print('Response:', ser.readline().decode())
"

# Change expression
echo -e "EXPR:thinking\n" > /dev/serial0

# Reset Pico
python3 -c "
import serial
ser = serial.Serial('/dev/ttyACM0', 115200)
ser.write(b'\x04')  # CTRL+D soft reset
"
```

---

## Files to Review

- `/home/tim/GairiHead/docs/SESSION_2025-11-12_PICO_NEOPIXEL_WIRING.md` - Full session notes
- `/home/tim/GairiHead/tests/test_pico_uart.py` - UART test script
- `/media/tim/CIRCUITPY/code.py` - Pico controller code

---

## Success Criteria

**Must Have:**
- [x] NeoPixels wired and working
- [ ] UART test passes (all expressions work)
- [ ] Can control eyes from Pi 5

**Next Phase:**
- [ ] PicoController module created
- [ ] Hardware coordinator integration
- [ ] Servo + eye expressions synced

---

## Troubleshooting Quick Reference

| Problem | Check | Fix |
|---------|-------|-----|
| No UART response | TX/RX wiring | Swap GP0/GP1 |
| Pico not found | USB connection | Replug USB, check /dev/ttyACM0 |
| Eyes flicker | Power supply | Check voltage (5.0V), upgrade to 3A |
| Wrong colors | Data corruption | Shorten wires, add 330Ω resistors |
| Pico won't boot | Code error | Reflash CircuitPython |

---

**Last Session**: Wired Pico + NeoPixels, tested standalone ✓
**This Session**: Test UART, integrate with main system
**Next Session**: Mount hardware, full system test

**Estimated Time**: 1-2 hours
**Difficulty**: Medium (debugging UART if issues arise)
**Blocker**: None (everything ready to test)
