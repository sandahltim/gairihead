# GairiHead Servo Wiring Diagram

**Visual reference for connecting servos to Pi 5 with M.2 HAT**

---

## Complete Wiring Overview

```
┌────────────────────────────────────────────────────────────────┐
│                    5V/2A POWER SUPPLY                          │
│                     (USB adapter or DC)                         │
└───────┬────────────────────────────────────────────┬───────────┘
        │                                            │
        │ +5V                                    GND │
        │                                            │
    ┌───┴────────────────────────────────────────────┴───┐
    │                                                     │
    │   RED wires                           BLACK wires  │
    │   (VCC)                                   (GND)    │
    │                                                     │
    ├─────→ Left Eyelid Servo VCC                        │
    ├─────→ Right Eyelid Servo VCC                       │
    ├─────→ Mouth Servo VCC                              │
    │                                                     │
    │                                    COMMON GROUND ←──┼───┐
    └─────────────────────────────────────────────────────┘   │
                                                               │
┌──────────────────────────────────────────────────────────────┴─┐
│                     RASPBERRY PI 5                             │
│                   (with M.2 HAT installed)                     │
│                                                                │
│  GPIO Header (40-pin):                                         │
│                                                                │
│   [1]  3.3V          [2]  5V                                   │
│   [3]  GPIO2         [4]  5V                                   │
│   [5]  GPIO3         [6]  GND ──────────────────────────────── COMMON GND
│   [7]  GPIO4         [8]  GPIO14 (UART TX)                     │
│   [9]  GND           [10] GPIO15 (UART RX)                     │
│   [11] GPIO17 ─────────────────────────→ Left Eyelid Signal    │
│   [12] GPIO18        [13] GPIO27 ───────→ Right Eyelid Signal  │
│   [14] GND           [15] GPIO22 ───────→ Mouth Signal         │
│   [16] GPIO23        [17] 3.3V                                 │
│   ...                                                          │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

---

## Servo Wire Colors

Most SG90 servos use this color scheme:
- **Brown/Black** = GND (Ground)
- **Red** = VCC (Power, 5V)
- **Orange/Yellow/White** = Signal (PWM control)

**⚠️ Some servos vary! Check your servo datasheet.**

---

## Connection Table

| Servo | Signal Wire | VCC Wire | GND Wire |
|-------|-------------|----------|----------|
| **Left Eyelid** | GPIO 17 (Pin 11) | 5V Supply | Common GND |
| **Right Eyelid** | GPIO 27 (Pin 13) | 5V Supply | Common GND |
| **Mouth** | GPIO 22 (Pin 15) | 5V Supply | Common GND |

---

## Step-by-Step Wiring

### 1. Power Supply Setup

**Option A: USB Power Adapter (Recommended)**
```
USB 5V/2A adapter
  ├─→ Cut off device end
  ├─→ Strip wires
  │   ├─→ Red wire = +5V
  │   └─→ Black wire = GND
  └─→ Connect to breadboard or terminal block
```

**Option B: Breadboard Power Module**
```
Breadboard power module
  ├─→ Plug in 9V-12V DC adapter
  ├─→ Set jumper to 5V output
  └─→ Use rails for +5V and GND
```

### 2. Servo Power Connections

Connect all servo VCC (red) wires together:
```
5V Supply (+) ─┬─→ Left Eyelid VCC (red)
               ├─→ Right Eyelid VCC (red)
               └─→ Mouth VCC (red)
```

Connect all servo GND (black/brown) wires together:
```
5V Supply (-) ─┬─→ Left Eyelid GND (black/brown)
               ├─→ Right Eyelid GND (black/brown)
               ├─→ Mouth GND (black/brown)
               └─→ Pi 5 GND (Pin 6, 9, 14, 20, 25, 30, 34, or 39)
                   ↑
                   CRITICAL: Common ground connection!
```

### 3. Signal Wire Connections

**Left Eyelid**:
- Orange/Yellow/White wire → GPIO 17 (Pin 11 on Pi 5 header)

**Right Eyelid**:
- Orange/Yellow/White wire → GPIO 27 (Pin 13 on Pi 5 header)

**Mouth**:
- Orange/Yellow/White wire → GPIO 22 (Pin 15 on Pi 5 header)

---

## Physical Layout (Top View)

```
                    ┌──────────────┐
                    │   Pi 5 Board │
                    │  with M.2 HAT│
                    │              │
      GPIO Header → ├──┐           │
                    │  │           │
                    │  │  ┌────────┤
                    │  │  │ M.2 SSD│
                    │  │  │        │
                    └──┼──┴────────┘
                       │
         ┌─────────────┼─────────────┐
         │                           │
         │  Pin 11 (GPIO 17) ────────┼──→ Left Eyelid Signal
         │  Pin 13 (GPIO 27) ────────┼──→ Right Eyelid Signal
         │  Pin 15 (GPIO 22) ────────┼──→ Mouth Signal
         │  Pin 6/9/14 (GND) ────────┼──→ Common Ground
         │                           │
         └───────────────────────────┘
```

---

## Testing Checklist

Before powering on:

- [ ] **Servo power** connected to external 5V supply (NOT Pi 5)
- [ ] **Common ground** connected between Pi 5 and servo supply
- [ ] **Signal wires** connected to GPIO 17, 27, 22
- [ ] **No servo VCC wires** touching Pi 5 5V pins
- [ ] **M.2 HAT** properly seated
- [ ] **Pi 5** has separate 5V/5A power supply

After wiring:

- [ ] Power supply voltage measured (should be 4.8-5.2V)
- [ ] No shorts between 5V and GND (use multimeter)
- [ ] Signal wires secure in GPIO header
- [ ] All ground connections solid

---

## Common Mistakes ⚠️

1. **Powering servos from Pi 5 GPIO**
   - ❌ NEVER connect servo VCC to Pi 5 5V pins
   - ✅ ALWAYS use separate power supply

2. **Missing common ground**
   - ❌ Servo GND not connected to Pi 5 GND
   - ✅ Both grounds must connect together

3. **Wrong signal pins**
   - ❌ Using GPIO 12/13/18 (old pins, conflicts with M.2 HAT)
   - ✅ Use GPIO 17/27/22 (new safe pins)

4. **Reversed servo wires**
   - Check servo wire colors match your servos
   - Most use Brown=GND, Red=VCC, Orange=Signal

5. **Loose connections**
   - Signal wires must make solid contact with GPIO pins
   - Use Dupont jumper wires for secure connection

---

## Troubleshooting

**Servos not moving**:
1. Check pigpio daemon: `sudo systemctl status pigpiod`
2. Verify 5V at servo VCC with multimeter
3. Confirm signal wires on correct GPIO pins

**Servos jittering**:
1. Power supply too weak (need 2A minimum)
2. Loose ground connection
3. Signal wire too long (>30cm can cause issues)

**Pi 5 rebooting**:
1. You're powering servos from Pi 5 (DON'T!)
2. Use separate servo power supply

**One servo works, others don't**:
1. Check individual signal wire connections
2. Verify GPIO pin numbers in config match wiring
3. Test each servo separately

---

## Parts Needed for Wiring

- **3x SG90 Servos** (with attached wires)
- **5V/2A Power Supply** (USB adapter or DC supply)
- **Breadboard or terminal block** (optional, for organizing connections)
- **6x Female-to-Female Dupont wires** (for GPIO connections)
- **Wire strippers** (if cutting power adapter)
- **Multimeter** (for testing voltage/continuity)
- **Small screwdriver** (for terminal blocks if used)

---

## Safety Notes

- Servos can get warm during extended use (normal)
- If servos get hot to touch, reduce duty cycle
- Don't force servo past mechanical stops
- Keep wiring away from moving parts
- Use proper gauge wire for power (22-24 AWG for servos)

---

## After Wiring Complete

Run the test script:
```bash
ssh tim@100.103.67.41
cd ~/GairiHead
source venv/bin/activate
sudo systemctl start pigpiod
python tests/test_servos.py
```

You should see:
1. Left eyelid sweeps slowly
2. Right eyelid sweeps slowly
3. Mouth sweeps slowly
4. Both eyes blink 3 times
5. Expression cycle through 6 states

**If all works**: Proceed to Pico + NeoPixel setup!

---

**Reference**: Based on Pi 5 GPIO pinout and M.2 HAT compatibility analysis
**Updated**: 2025-11-06 (M.2 HAT safe pins)
