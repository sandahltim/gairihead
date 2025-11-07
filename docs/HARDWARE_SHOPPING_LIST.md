# GairiHead Hardware Shopping List

**Total estimated cost**: ~$250-300

---

## Core Components (Ordered ✅)

### Compute
- **Raspberry Pi 5 (4GB or 8GB)** - $60-80
  - Already installed at 100.103.67.41
  - Running Ubuntu with M.2 HAT

- **Raspberry Pi Pico W** - $6
  - For NeoPixel ring control (2x GPIO pins)
  - UART connection to Pi 5

### Display (Eyes)
- **2x WS2812B NeoPixel RGB Rings (12 pixels)** - $6-8 each
  - Left eye: Connected to Pico GP2
  - Right eye: Connected to Pico GP3
  - 5V power required

### Movement
- **3x SG90 Micro Servos** - $2-3 each
  - Left eyelid: GPIO 17
  - Right eyelid: GPIO 27
  - Mouth: GPIO 22
  - ⚠️ Need separate 5V/2A power supply

### Vision
- **Raspberry Pi Camera Module 3** - $25
  - Direct CSI connection to Pi 5
  - 11.9MP, wide angle
  - No GPIO pins needed

### Audio
- **USB Microphone** - $15-20
  - Recommended: Blue Snowflake or similar
  - Any USB mic will work

- **USB Speaker** - $10-15
  - Compact powered speaker
  - 3.5mm or USB connection

---

## Power & Accessories

### Power Supply
- **Pi 5 Power Supply (5V/5A USB-C)** - $12
  - Official Raspberry Pi power supply recommended

- **Servo Power Supply (5V/2A)** - $8-10
  - USB power adapter (cheap option)
  - OR DC barrel jack supply
  - ⚠️ CRITICAL: Must share common ground with Pi 5

### Connectivity
- **M.2 HAT + SSD** - Already installed ✅
  - Using M.2-safe GPIO pins (17, 27, 22)

- **UART Connection (Pi 5 ↔ Pico)**
  - 3x Dupont jumper wires (TX, RX, GND)
  - Included with Pico or separate pack for $3

---

## 3D Printed Parts (STL files needed)

Based on Bubo-2T template (kevsrobots.com/blog/bubo-2t.html):

- **Head Shell** (top/bottom)
- **Eye Mounts** (2x for NeoPixel rings)
- **Eyelid Servo Mounts** (2x)
- **Mouth Servo Mount**
- **Camera Mount** (Pi Camera Module 3)
- **Internal Frame/Brackets**

**Filament needed**: ~200-300g PLA
**Print time**: ~12-20 hours total

---

## Optional Upgrades

### Better Audio
- **ReSpeaker 2-Mics Pi HAT** - $15
  - Better far-field voice detection
  - Conflicts with some GPIO pins (check compatibility)

### Better Voice
- **I2S Amplifier + Speaker** - $10-15
  - Better audio quality than USB
  - Uses I2S pins (GPIO 18, 19, 21)

### Power Management
- **UPS HAT for Pi 5** - $25-35
  - Battery backup during power loss
  - Clean shutdown capability

---

## Where to Buy

**US Vendors**:
- Raspberry Pi official: rpilocator.com
- Adafruit: adafruit.com (NeoPixels, servos, breakouts)
- Amazon: Quick delivery, bulk servos/jumpers
- Micro Center: In-store pickup if nearby

**Note**: Check what's already ordered before purchasing duplicates!

---

## Assembly Tools Needed

- Soldering iron (for NeoPixel/Pico connections)
- Small screwdriver set
- Wire strippers
- Heat shrink tubing or electrical tape
- Multimeter (for power/ground testing)
- Hot glue gun (optional, for cable management)

---

**Status**: Core components ordered 2025-11-06
**Next**: Wait for delivery, test servos when they arrive
