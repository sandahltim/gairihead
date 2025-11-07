# GairiHead Hardware Pin Assignments

**Pi 5 with M.2 HAT - Pin assignments that avoid conflicts**

---

## GPIO Pin Usage

### Servos (PWM Control)

**Left Eyelid Servo**:
- GPIO: **17** (Pin 11)
- Signal wire: Yellow/White
- Power: 5V external supply
- Ground: Common ground with Pi 5

**Right Eyelid Servo**:
- GPIO: **27** (Pin 13)
- Signal wire: Yellow/White
- Power: 5V external supply
- Ground: Common ground with Pi 5

**Mouth Servo**:
- GPIO: **22** (Pin 15)
- Signal wire: Yellow/White
- Power: 5V external supply
- Ground: Common ground with Pi 5

---

## Pi 5 GPIO Pinout (40-pin header)

```
     3.3V [ 1] [ 2] 5V
    GPIO2 [ 3] [ 4] 5V
    GPIO3 [ 5] [ 6] GND
    GPIO4 [ 7] [ 8] GPIO14 (UART TX)
      GND [ 9] [10] GPIO15 (UART RX)
   GPIO17 [11] [12] GPIO18        ← LEFT EYELID (GPIO 17)
   GPIO27 [13] [14] GND           ← RIGHT EYELID (GPIO 27)
   GPIO22 [15] [16] GPIO23        ← MOUTH (GPIO 22)
     3.3V [17] [18] GPIO24
   GPIO10 [19] [20] GND
    GPIO9 [21] [22] GPIO25
   GPIO11 [23] [24] GPIO8
      GND [25] [26] GPIO7
    GPIO0 [27] [28] GPIO1
    GPIO5 [29] [30] GND
    GPIO6 [31] [32] GPIO12
   GPIO13 [33] [34] GND
   GPIO19 [35] [36] GPIO16
   GPIO26 [37] [38] GPIO20
      GND [39] [40] GPIO21
```

---

## M.2 HAT Considerations

**Pins typically used by M.2 HATs**:
- PCIe lane (dedicated, not on GPIO header)
- Power control: Sometimes GPIO 0-11 range
- Status LEDs: Sometimes GPIO 12-13

**Our servo pins (17, 27, 22)**:
- ✅ Safe - Outside typical M.2 HAT usage
- ✅ PWM capable
- ✅ Easy access on GPIO header (pins 11, 13, 15)

---

## Pico UART (when added)

**Pi 5 → Pico Communication**:
- TX: GPIO 14 (Pin 8)
- RX: GPIO 15 (Pin 10)
- GND: Pin 6, 9, 14, 20, 25, 30, 34, or 39

**Pico → NeoPixel Rings**:
- Left eye: Pico GP2
- Right eye: Pico GP3

---

## Power Requirements

**⚠️ CRITICAL - Separate Power Supply for Servos**

**DO NOT** power servos from Pi 5 GPIO:
- Pi 5 GPIO: Max 500mA total
- 3x SG90 servos: Can pull 500-800mA each under load

**Correct wiring**:
```
5V/2A Power Supply
  ├─→ Servo 1 VCC (red wire)
  ├─→ Servo 2 VCC (red wire)
  ├─→ Servo 3 VCC (red wire)
  └─→ GND (black wire) ───┐
                           ├─→ Common ground
Pi 5 GND ─────────────────┘

Pi 5 GPIO 17 ─→ Servo 1 Signal (yellow/white wire)
Pi 5 GPIO 27 ─→ Servo 2 Signal (yellow/white wire)
Pi 5 GPIO 22 ─→ Servo 3 Signal (yellow/white wire)
```

**Power supply recommendations**:
- 5V/2A USB power adapter (cheap, easy)
- Separate DC barrel jack supply
- Common ground between Pi 5 and servo supply is REQUIRED

---

## Camera (when added)

**Pi Camera Module 3**:
- CSI connector on Pi 5 (dedicated, no GPIO conflict)
- Power: From CSI connector
- No additional wiring needed

---

## USB Devices (no GPIO pins used)

**USB Microphone**: Any USB port
**USB Speaker**: Any USB port

---

## Wiring Checklist

Before powering on:

- [ ] Servos powered from **external 5V supply** (NOT Pi 5)
- [ ] Common ground connected between Pi 5 and servo supply
- [ ] Servo signal wires connected to GPIO 17, 27, 22
- [ ] No servo power wires connected to Pi 5 5V pins
- [ ] M.2 HAT properly seated and secured
- [ ] Pi 5 has separate 5V/5A power supply

---

## Testing Order

1. **Power test**: Pi 5 boots with M.2 HAT (no servos)
2. **Servo power test**: Servos powered separately, no signal
3. **Signal test**: Connect signal wires, run test_servos.py
4. **Full test**: All servos moving smoothly

---

**Updated**: 2025-11-06
**Pins changed**: Moved from GPIO 12/13/18 to 17/27/22 (M.2 HAT compatibility)
