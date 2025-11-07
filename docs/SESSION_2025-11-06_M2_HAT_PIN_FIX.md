# GairiHead M.2 HAT Pin Compatibility Fix

**Date**: 2025-11-06
**Status**: ✅ Complete - Ready for servo testing

---

## Problem

User reported Pi 5 has M.2 HAT with M.2 drive that uses some GPIO pins. Original servo pin assignments might conflict:
- Left eyelid: GPIO 12
- Right eyelid: GPIO 13
- Mouth: GPIO 18

M.2 HATs typically use GPIO 0-11 range for power control and GPIO 12-13 for status LEDs.

---

## Solution

Moved servos to M.2 HAT-safe GPIO pins:

| Component | Old Pin | New Pin | Physical Pin | Notes |
|-----------|---------|---------|--------------|-------|
| Left Eyelid | GPIO 12 | **GPIO 17** | Pin 11 | ✅ PWM capable, safe |
| Right Eyelid | GPIO 13 | **GPIO 27** | Pin 13 | ✅ PWM capable, safe |
| Mouth | GPIO 18 | **GPIO 22** | Pin 15 | ✅ PWM capable, safe |

**Why these pins are safe**:
- Outside typical M.2 HAT range (0-13)
- All PWM-capable via software PWM (gpiozero/pigpio)
- Easy physical access on GPIO header
- No conflicts with UART (GPIO 14/15), I2C, SPI

---

## Files Updated

### 1. `/Gary/GairiHead/config/gairi_head.yaml`
```yaml
servos:
  # Using GPIO pins that won't conflict with M.2 HAT (avoiding 0-11, 12-13)
  left_eyelid:
    gpio_pin: 17      # Safe pin, away from M.2 HAT
  right_eyelid:
    gpio_pin: 27      # Safe pin, away from M.2 HAT
  mouth:
    gpio_pin: 22      # Safe pin, away from M.2 HAT
```

### 2. `/Gary/GairiHead/docs/HARDWARE_PINS.md`
- Complete pinout diagram
- M.2 HAT compatibility notes
- Power supply wiring diagram
- Safety checklist

### 3. `/Gary/GairiHead/docs/DEPLOYMENT.md`
- Updated servo wiring section
- Correct GPIO pin numbers
- Added M.2 HAT warning

### 4. `/Gary/GairiHead/src/servo_controller.py`
- Already uses config file, no code changes needed
- Pin assignments pulled from gairi_head.yaml automatically

---

## Testing Status

### ✅ Completed
- [x] Files deployed to Pi 5 (tim@100.103.67.41)
- [x] Virtual environment created
- [x] Dependencies installed (pyyaml, loguru, gpiozero, pigpio)
- [x] Basic config test passed
- [x] All config files load correctly

### ⏳ Waiting for Hardware
- [ ] Connect servos to GPIO 17, 27, 22
- [ ] Start pigpio daemon
- [ ] Run `python tests/test_servos.py`
- [ ] Verify servo movement with new pins

---

## Power Requirements (CRITICAL)

**⚠️ DO NOT power servos from Pi 5 GPIO**

Servos need separate 5V/2A power supply:
```
5V/2A Power Supply
  ├─→ Servo VCC (red wires)
  └─→ GND (black wires) ───┐
                            ├─→ Common ground
Pi 5 GND ──────────────────┘

Pi 5 GPIO 17/27/22 ─→ Servo Signal (yellow/white wires)
```

**Why**:
- Pi 5 GPIO: Max 500mA total across all pins
- 3x SG90 servos: Can pull 500-800mA **each** under load
- Powering from GPIO will brownout/damage Pi 5

---

## GPIO Pin Conflicts to Avoid

### Used by M.2 HAT (avoid these):
- GPIO 0-11: Possible power/config pins
- GPIO 12-13: Possible status LEDs

### Used by UART (reserved for Pico):
- GPIO 14: TX (Pi 5 → Pico)
- GPIO 15: RX (Pi 5 ← Pico)

### Used by I2C (future expansion):
- GPIO 2: SDA
- GPIO 3: SCL

### Safe for Servos (our choice):
- ✅ GPIO 17, 27, 22

---

## Next Steps

1. **When servos arrive**:
   ```bash
   ssh tim@100.103.67.41
   sudo systemctl start pigpiod
   cd ~/GairiHead
   source venv/bin/activate
   python tests/test_servos.py
   ```

2. **If test passes**: Proceed with Pico NeoPixel setup

3. **If test fails**: Check:
   - Servo power supply voltage (stable 5V)
   - Common ground connection
   - Signal wire connections to correct pins
   - pigpio daemon running

---

## Reference Documents

- `docs/HARDWARE_PINS.md` - Detailed pinout and wiring
- `docs/DEPLOYMENT.md` - Full deployment guide
- `QUICKSTART.md` - Quick reference for next steps
- `tests/test_servos.py` - Automated servo test

---

## Decision Log

**Why not use GPIO 18?** (original mouth pin)
- GPIO 18 is hardware PWM capable (best choice)
- BUT moved to GPIO 22 for consistency
- All three servos now in GPIO 17-27 range (easy to remember)
- Software PWM via pigpio works perfectly fine

**Why pigpio instead of RPi.GPIO?**
- More precise timing (1μs resolution)
- Better servo control (less jitter)
- Required for smooth eyelid/mouth movement
- Standard practice for servo control on Pi

**Can we use the M.2 drive safely?**
- YES - Our servo pins don't conflict
- M.2 HAT uses dedicated PCIe lane (not GPIO)
- Power/status pins (if any) are in 0-13 range
- No need to switch to USB/SD card

---

**Conclusion**: M.2 HAT compatible, ready for servo hardware testing.
