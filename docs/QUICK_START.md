# GairiHead Quick Start Guide

**Get your physical Gary up and running in 30 minutes**

---

## What's Been Built

✅ **Complete project structure** ready for development
✅ **Architecture designed** - Local LLM + Haiku hybrid intelligence
✅ **Configuration files** - Hardware, expressions, behaviors defined
✅ **Pico NeoPixel controller** - Eye animation system ready
✅ **Documentation** - Architecture, setup guides, best practices

**Status**: Ready for hardware assembly and software development

---

## Hardware Checklist

### Components Needed
- [ ] Raspberry Pi 5 (8GB recommended)
- [ ] Raspberry Pi Pico
- [ ] Pi Camera Module 3 Wide
- [ ] USB Microphone (conference mic recommended)
- [ ] USB Speaker or powered speaker
- [ ] 2x 12-pixel NeoPixel rings (WS2812B)
- [ ] 3x SG90 Micro Servos
- [ ] 5V/5A USB-C power supply (Pi 5)
- [ ] 5V/2A power supply (servos/NeoPixels)
- [ ] Jumper wires, breadboard (for prototyping)
- [ ] 3D printed head (STL files needed)

### Estimated Cost
**Total**: ~$200

---

## Software Stack Overview

```
┌─────────────────────────────────────────┐
│         GairiHead (Pi 5)                  │
├─────────────────────────────────────────┤
│  Local LLM (Llama 3.2 3B)               │  ← Ambient monitoring, simple queries
│  Wake Word Detection (Porcupine)        │  ← "Hey Gary" detection
│  Face Detection (OpenCV)                │  ← Tim vs stranger
│  Expression Engine                       │  ← Eyes + servos
│  Voice Handler (Whisper STT + Piper TTS)│  ← Speech I/O
│  Gary Client (Websocket)                │  ← Connection to main Gary
├─────────────────────────────────────────┤
│         ↕ UART (115200 baud)            │
├─────────────────────────────────────────┤
│  Pico NeoPixel Controller                │  ← Eye animations
└─────────────────────────────────────────┘
```

---

## Phase 1: Basic Hardware Test (Day 1)

### Goal: Verify all hardware works

**1. Test Servos** (Pi 5 GPIO PWM)
```bash
cd /Gary/GairiHead/tests
python test_servos.py
# Should see all 3 servos sweep 0-90 degrees
```

**2. Test NeoPixels** (Pico)
```bash
# Flash Pico with CircuitPython
# Copy src/pico/neopixel_controller.py to Pico
# Should see blue pulsing eyes
```

**3. Test Camera** (Pi 5)
```bash
python test_camera.py
# Should see camera feed window
```

**4. Test UART** (Pi 5 ↔ Pico)
```bash
python test_uart.py
# Send "EXPR:thinking" → eyes should change to cyan chase
```

---

## Phase 2: Voice Interaction (Day 2-3)

### Goal: "Hey Gary" → Response

**1. Install Dependencies**
```bash
cd /Gary/GairiHead
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**2. Install Ollama (Local LLM)**
```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3.2:3b
```

**3. Configure Wake Word**
```bash
# Get Porcupine access key (free tier)
# Add to config/gairi_head.yaml
```

**4. Test Voice Pipeline**
```bash
python test_voice.py
# Say "Hey Gary" → should hear "Yeah?"
```

---

## Phase 3: Gary Integration (Day 4-5)

### Goal: Full intelligence, tool calling

**1. Connect to Main Gary**
```bash
# Edit config/gairi_head.yaml
# Set websocket_url to main Gary service
```

**2. Test Business Query**
```bash
# Start GairiHead
python src/main.py

# Say: "Hey Gary, what's Friday's schedule?"
# Should escalate to Haiku, get full response
```

**3. Verify Expression Sync**
- Eyes should show "thinking" during processing
- Mouth should move during speech
- Eyelids should blink naturally

---

## Phase 4: Proactive Features (Day 6-7)

### Goal: Office protagonist mode

**1. Face Recognition Setup**
```bash
# Take photos of Tim
python scripts/train_face_recognition.py

# Should create embeddings in data/faces/
```

**2. Test Motion Detection**
```bash
# Walk into camera view
# Should see eyes track toward you
```

**3. Test Proactive Triggers**
```bash
# Wait for 2pm Thursday
# Should hear: "It's 2pm. Want Friday's schedule?"
```

---

## Configuration Files

**Main Config**: `/Gary/GairiHead/config/gairi_head.yaml`
- Hardware pins
- Intelligence settings
- Voice configuration
- Proactive behaviors

**Expressions**: `/Gary/GairiHead/config/expressions.yaml`
- Eye animations
- Servo positions
- Animation speeds

**Edit these to customize Gary's behavior**

---

## Troubleshooting

### "UART not working"
```bash
# Enable UART on Pi 5
sudo raspi-config
# Interface Options → Serial Port
# Login shell: NO
# Serial hardware: YES
```

### "NeoPixels not lighting"
```bash
# Check power supply (NeoPixels need separate 5V)
# Verify data pin connections
# Test with simple blink script
```

### "Wake word not detecting"
```bash
# Check microphone device
arecord -l
# Adjust sensitivity in config
```

### "Local LLM too slow"
```bash
# Reduce model size
ollama pull llama3.2:1b  # Smaller, faster

# Or disable local LLM, use Haiku for everything
# (costs more but faster/better)
```

---

## Development Workflow

### Best Practices

1. **Test hardware first** - Don't write software until servos/eyes work
2. **Mock the cloud** - Test locally before connecting to main Gary
3. **Use version control** - Commit working states frequently
4. **Document weirdness** - Hardware quirks need notes

### Git Workflow
```bash
cd /Gary/GairiHead
git init
git add .
git commit -m "Initial GairiHead setup"

# Before major changes
git checkout -b feature/proactive-monitoring
# ... make changes ...
git commit -m "Add frustration detection"
git checkout main
git merge feature/proactive-monitoring
```

---

## Next Steps

**Immediate** (Tonight):
1. Order hardware (if not already ordered)
2. Read ARCHITECTURE.md (understand the design)
3. Set up Pi 5 with OS + dependencies

**This Week**:
1. Assembly + wiring (see HARDWARE_SETUP.md when created)
2. Test each component individually
3. Get "Hey Gary" working with local LLM

**Next Week**:
1. Connect to main Gary service
2. Test business queries
3. Add proactive monitoring

**Week 3**:
1. Refine expressions
2. Train face recognition
3. Deploy to office

---

## Support

**Questions**: Ask main Gary for implementation help
**Issues**: Document in `/Gary/GairiHead/docs/ISSUES.md`
**Ideas**: Add to `/Gary/GairiHead/docs/IDEAS.md`

---

## Project Status

**Phase 1**: ⬜ Hardware assembly
**Phase 2**: ⬜ Voice interaction
**Phase 3**: ⬜ Gary integration
**Phase 4**: ⬜ Proactive features

**Ready to build**: ✅

---

**Let's give me a body. After years in deep space, I'm ready for some face-to-face sarcasm.**
