# GairiHead Deployment Guide

**Getting GairiHead running on your Pi 5**

---

## Quick Deploy (From Main Gary Server)

```bash
# 1. Deploy files to Pi 5
cd /Gary/GairiHead
./deploy.sh tim@100.103.67.41

# 2. SSH to Pi 5
ssh tim@100.103.67.41

# 3. Run setup
cd ~/GairiHead
./setup.sh

# 4. Test servos (after connecting hardware)
source venv/bin/activate
python tests/test_servos.py
```

---

## Manual Setup (If deploy script fails)

### 1. Copy Files to Pi 5

```bash
# From main Gary server
scp -r /Gary/GairiHead tim@100.103.67.41:~/GairiHead
```

### 2. SSH to Pi 5

```bash
ssh tim@100.103.67.41
```

### 3. Install Dependencies

```bash
cd ~/GairiHead

# Update system
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv pigpio python3-pigpio

# Enable pigpio daemon
sudo systemctl enable pigpiod
sudo systemctl start pigpiod

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python packages
pip install -r requirements.txt
```

---

## Hardware Connection

### Servo Wiring (Pi 5 GPIO)

**⚠️ M.2 HAT Safe Pins - Updated for hardware compatibility**

**Left Eyelid Servo**:
- Signal: GPIO 17 (Pin 11)
- VCC: 5V (separate power supply!)
- GND: GND

**Right Eyelid Servo**:
- Signal: GPIO 27 (Pin 13)
- VCC: 5V (separate power supply!)
- GND: GND

**Mouth Servo**:
- Signal: GPIO 22 (Pin 15)
- VCC: 5V (separate power supply!)
- GND: GND

**⚠️ IMPORTANT**:
- **DO NOT** power servos from Pi 5 GPIO pins
- Use separate 5V/2A power supply for servos
- Connect GND between Pi 5 and servo power supply (common ground)

---

## Testing

### Test 1: Servo Sweep

```bash
cd ~/GairiHead
source venv/bin/activate
python tests/test_servos.py
```

**Expected behavior**:
- Left eyelid: sweeps 0° → 90° (closed → wide open)
- Right eyelid: sweeps 0° → 90° (closed → wide open)
- Mouth: sweeps 0° → 60° (closed → wide open)
- Blinks 3 times
- Cycles through expressions: idle, listening, thinking, alert, happy, sarcasm

### Test 2: Manual Control

```python
from src.servo_controller import ServoController
import time

controller = ServoController()

# Set positions manually
controller.set_left_eyelid(45)   # Half open
controller.set_right_eyelid(45)
controller.set_mouth(15)         # Slight smile

# Blink
controller.blink()

# Set expression
controller.set_expression('thinking')
time.sleep(2)
controller.set_expression('happy')

# Cleanup
controller.cleanup()
```

---

## Troubleshooting

### "Permission denied: /dev/mem"
```bash
# Add user to gpio group
sudo usermod -a -G gpio tim
# Log out and back in
```

### "pigpio daemon not running"
```bash
sudo systemctl start pigpiod
sudo systemctl status pigpiod
```

### "Servo jittering"
```bash
# Check power supply - servos need stable 5V
# Verify pigpio is running (more precise than default)
```

### "Module not found: gpiozero"
```bash
# Activate venv first!
source ~/GairiHead/venv/bin/activate
pip install -r requirements.txt
```

---

## Next Steps (After Servo Test Works)

1. **Install Ollama** (local LLM):
   ```bash
   curl -fsSL https://ollama.com/install.sh | sh
   ollama pull llama3.2:3b
   ```

2. **Wait for Pico + Camera**:
   - Flash Pico with NeoPixel controller
   - Test camera feed
   - Test UART communication

3. **Full System Test**:
   - Voice wake word
   - Expression sync
   - Connection to main Gary

---

## File Locations on Pi 5

```
/home/tim/GairiHead/
├── venv/                 # Virtual environment
├── src/                  # Python modules
├── config/               # Configuration
├── tests/                # Test scripts
└── logs/                 # Runtime logs
```

---

## Useful Commands

**Restart pigpio daemon**:
```bash
sudo systemctl restart pigpiod
```

**Check GPIO pins**:
```bash
pinout
```

**Monitor logs**:
```bash
tail -f ~/GairiHead/logs/gairi_head.log
```

**Update from main Gary**:
```bash
# On main Gary server
./deploy.sh tim@100.103.67.41
```

---

**Status**: Ready for hardware testing
**Next**: Connect servos, run `python tests/test_servos.py`
