# GairiHead Quick Start Guide

**Status**: Software ready, waiting for servo hardware

---

## Current State ✅

- ✅ Pi 5 running at 100.103.67.41 (Ubuntu + M.2 HAT)
- ✅ Project deployed to ~/GairiHead
- ✅ Virtual environment created with dependencies
- ✅ Config files ready with M.2-safe GPIO pins
- ✅ Basic tests passing

## Next Steps (When Servos Arrive)

### 1. Wire Servos

**⚠️ CRITICAL: Use separate 5V power supply for servos!**

Connect servos to **M.2 HAT-safe GPIO pins**:

```
Left Eyelid Servo:
  Signal (Yellow/White) → GPIO 17 (Pin 11)
  VCC (Red)            → 5V power supply
  GND (Black/Brown)    → Common ground

Right Eyelid Servo:
  Signal (Yellow/White) → GPIO 27 (Pin 13)
  VCC (Red)            → 5V power supply
  GND (Black/Brown)    → Common ground

Mouth Servo:
  Signal (Yellow/White) → GPIO 22 (Pin 15)
  VCC (Red)            → 5V power supply
  GND (Black/Brown)    → Common ground

Common Ground:
  Pi 5 GND (any GND pin) ←→ Servo power supply GND
```

**Reference**: See `docs/HARDWARE_PINS.md` for detailed pinout

### 2. Start pigpio Daemon

```bash
ssh tim@100.103.67.41
sudo systemctl start pigpiod
sudo systemctl enable pigpiod  # Auto-start on boot
```

### 3. Test Servos

```bash
ssh tim@100.103.67.41
cd ~/GairiHead
source venv/bin/activate
python tests/test_servos.py
```

**Expected behavior**:
- Left/right eyelids sweep 0° → 90° (closed → wide open)
- Mouth sweeps 0° → 60° (closed → wide open)
- 3 blinks
- Expression cycle: idle → listening → thinking → alert → happy → sarcasm

### 4. Troubleshooting

**"pigpio daemon not running"**:
```bash
sudo systemctl restart pigpiod
sudo systemctl status pigpiod
```

**"Permission denied"**:
```bash
sudo usermod -a -G gpio tim
# Log out and back in
```

**"Servo jittering"**:
- Check 5V power supply is stable (need 2A minimum)
- Verify common ground between Pi 5 and servo power

---

## After Servos Work

### Install Ollama (Local LLM)
```bash
ssh tim@100.103.67.41
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3.2:3b
```

### Wait for Remaining Hardware
- [ ] Pico W (for NeoPixel RGB eye rings)
- [ ] Pi Camera Module 3
- [ ] USB microphone
- [ ] USB speaker

### Then Test Full System
```bash
cd ~/GairiHead
source venv/bin/activate
python src/main.py
```

---

## Quick Commands

**Update from main Gary server**:
```bash
# On main Gary server
cd /Gary/GairiHead
./deploy.sh tim@100.103.67.41
```

**Check logs**:
```bash
ssh tim@100.103.67.41
tail -f ~/GairiHead/logs/gairi_head.log
```

**GPIO pinout reference**:
```bash
ssh tim@100.103.67.41
pinout
```

---

**Hardware ordered**: 2025-11-06
**Software ready**: 2025-11-06
**Next milestone**: Servo testing
