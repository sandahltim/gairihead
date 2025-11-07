# GairiHead - Expressive Robot Head

<div align="center">

**TARS-like personality • 24 expressions • Smooth movement • Contextual memory**

![Version](https://img.shields.io/badge/version-2.0-blue.svg)
![Platform](https://img.shields.io/badge/platform-Raspberry%20Pi%205-red.svg)
![Python](https://img.shields.io/badge/python-3.11+-green.svg)

Physical robot head with expressive personality for office presence and ambient intelligence.

Integrates with [Gary](https://github.com/yourusername/gary) via websocket API.

</div>

---

## Features

### 🎭 Expressive Personality
- **24 emotional states** - From deadpan to celebration
- **18 eye animations** - Rainbow, spinner, sparkle, morse code, and more
- **Smooth movement** - Natural easing curves, not robotic jerks
- **TARS character** - Dry wit, competent, subtly caring

### 🤖 Autonomous Behaviors
- **Personality quirks** - Winks after sarcasm (15%), occasional sighs
- **Contextual memory** - Remembers last 3 expressions, mood drift
- **Natural variation** - Blink timing varies ±30% for realism
- **Time awareness** - Morning grumpy, Thursday planning energy

### 🧠 Two-Tier Intelligence
- **Local LLM** (Llama 3.2 3B) - Fast, free, 60% of queries
- **Cloud LLM** (Claude Haiku 4.5) - Complex reasoning, 40% of queries
- **Cost**: <$10/month vs $50+ all-cloud

### 📺 Visual Feedback
- **Arduino Display** - 2.8" TFT touchscreen with real-time conversation view
- **Touch interface** - View switching (Conversation, Status, Debug)
- **Expression emoji** - Shows current emotional state
- **Authorization display** - Color-coded security levels (green/yellow/red)

### 📡 Integration
- **Websocket API** - Remote control from main Gary system
- **Camera** - Logitech C920 (USB) or Pi Camera Module 3
- **Face recognition** - Authorization levels with training data
- **Voice I/O** - Whisper STT, pyttsx3 TTS - **WORKING**

---

## Quick Start

### Prerequisites
- Raspberry Pi 5 (4GB+)
- 3x SG90 servo motors
- Arduino Mega 2560 + TP28017 2.8" TFT HAT (for display)
- 2x WS2812B NeoPixel rings (12 pixels each)
- Raspberry Pi Pico 2 (for NeoPixel control)
- USB camera (Logitech C920 or equivalent)
- USB microphone + speaker (EMEET OfficeCore M0 Plus recommended)
- 5V/2A power supply for servos (separate from Pi!)

### Installation

```bash
# Clone repo
git clone <repo-url> ~/gairihead
cd ~/gairihead

# Run setup (installs dependencies, configures services)
./setup.sh

# Deploy to Pi 5 (from development machine)
./deploy.sh tim@100.103.67.41
```

### First Test

```bash
# SSH to Pi 5
ssh tim@100.103.67.41
cd ~/gairihead
source venv/bin/activate

# Start pigpio daemon (for servos)
sudo systemctl start pigpiod

# Test servos
python tests/test_servos.py

# Start websocket server
python src/gairi_head_server.py
```

### Voice Interaction

```bash
# Interactive mode (button-triggered voice)
cd ~/GairiHead
source venv/bin/activate
python main.py --mode interactive

# Press Enter to trigger voice interaction
# Speak when you see "listening" on Arduino display
# Your conversation will appear on the display
```

---

## Hardware Setup

### GPIO Pinout (M.2 HAT Safe)
```
GPIO 17 (Pin 11) → Left Eyelid Servo
GPIO 27 (Pin 13) → Right Eyelid Servo
GPIO 22 (Pin 15) → Mouth Servo
GPIO 14 (TX)     → Pico 2 UART RX
GPIO 15 (RX)     → Pico 2 UART TX
```

### Arduino Mega 2560 (Display Controller)
```
Connection: USB to Pi 5 (/dev/ttyACM0)
Display: TP28017 2.8" TFT HAT (240x320, ILI9341 controller)
Touch Pins: YP=A3, XM=A2, YM=9, XP=8
Library: MCUFRIEND_kbv (8-bit parallel interface)
Baudrate: 115200
Protocol: JSON over serial

Views:
  - Conversation: User/Gairi text with expression emoji
  - Status: User auth, confidence, system state
  - Debug: LLM tier, tools, response time
```

### Power Requirements
- **Pi 5**: USB-C 5V/5A (official power supply)
- **Arduino Mega**: Powered via USB from Pi 5
- **Servos**: SEPARATE 5V/2A supply (do NOT power from Pi!)
- **Common ground** between Pi and servo supply

See [docs/WIRING_DIAGRAM.md](docs/WIRING_DIAGRAM.md) for complete setup

---

## Expression Guide

### Core States
- `idle` - Default calm monitoring
- `listening` - Actively receiving input
- `thinking` - Processing local queries
- `processing` - Cloud escalation (purple eyes)
- `alert` - Important information

### TARS Personality ⭐
- `sarcasm` - Amber side-eye, may wink after
- `deadpan` - Flat delivery of humor
- `unimpressed` - Not buying it
- `disapproval` - One eyebrow raised
- `calculating` - Rapid cyan spinner

### Emotions
- `happy` / `amused` / `pride` - Positive range
- `concerned` / `frustrated` / `confused` - Negative range
- `celebration` - Rainbow party mode!
- `sheepish` - Oops, embarrassed

### Usage
```python
from src.expression_engine import ExpressionEngine

engine = ExpressionEngine()
engine.set_expression('sarcasm')  # May wink!
engine.micro_reaction('surprise')  # Brief flash
engine.celebration_mode(duration=5.0)  # Rainbow!
```

See [docs/EXPRESSIONS_GUIDE.md](docs/EXPRESSIONS_GUIDE.md) for complete reference.

---

## Architecture

### Software Components
```
┌─────────────────────────────────────┐
│     gairi_head_server.py            │
│     (Websocket API on port 8766)    │
└──────────┬──────────────────────────┘
           │
     ┌─────┴─────┐
     │           │
┌────▼────┐ ┌───▼──────────┐
│Expression│ │LLM Tier      │
│Engine    │ │Manager       │
│(v2.0)    │ │(Local+Cloud) │
└────┬─────┘ └──────────────┘
     │
  ┌──┴───────────┬─────────────┬────────────┐
  │              │             │            │
┌─▼───────┐ ┌───▼────┐ ┌──────▼──┐ ┌──────▼──────┐
│Servo    │ │NeoPixel│ │Vision   │ │Voice (TBD)  │
│Control  │ │(Pico 2)│ │Handler  │ │             │
└─────────┘ └────────┘ └─────────┘ └─────────────┘
```

### Integration with Gary
```
┌──────────────────┐         Websocket         ┌─────────────┐
│  Main Gary       │◄─────────────────────────►│  GairiHead  │
│  (Server)        │   ws://100.103.67.41:8766 │  (Pi 5)     │
│                  │                            │             │
│ gairi_head_tool  │                            │ gairi_head_ │
│     .py          │                            │  server.py  │
└──────────────────┘                            └─────────────┘
```

**Communication**: Network-separated, language-agnostic websocket protocol

---

## API Reference

### Websocket Commands

**Connect**: `ws://100.103.67.41:8766`

```json
// Capture snapshot
{"action": "capture_snapshot", "params": {"quality": 85}}

// Detect faces
{"action": "detect_faces", "params": {}}

// Record audio
{"action": "record_audio", "params": {"duration": 3.0}}

// Set expression
{"action": "set_expression", "params": {"expression": "sarcasm"}}

// Get status
{"action": "get_status", "params": {}}
```

See [docs/WEBSOCKET_INTEGRATION.md](docs/WEBSOCKET_INTEGRATION.md) for full API.

---

## Development

### Project Structure
```
gairihead/
├── src/
│   ├── gairi_head_server.py       # Websocket server
│   ├── expression_engine.py       # Emotional state (v2.0)
│   ├── servo_controller.py        # Smooth servo control
│   ├── camera_manager.py          # USB/Pi camera
│   ├── vision_handler.py          # Face detection
│   └── llm_tier_manager.py        # Local/cloud LLM
├── config/
│   ├── gairi_head.yaml            # Hardware config
│   └── expressions.yaml           # 24 expressions
├── tests/
│   ├── test_servos.py
│   ├── test_camera.py
│   └── test_gpio_simple.py
└── docs/
    └── EXPRESSIONS_GUIDE.md       # 650+ line reference
```

### Deployment

```bash
# Automated
./deploy.sh tim@100.103.67.41

# Manual
rsync -av --exclude='.git' . tim@100.103.67.41:~/gairihead/
ssh tim@100.103.67.41 "systemctl --user restart gairihead"
```

---

## Roadmap

### ✅ Complete (v2.0)
- 24 expressions with TARS personality
- Smooth servo movement with easing
- Contextual memory & mood drift
- Personality quirks (winks, sighs)
- Websocket API & Gary integration
- Camera & face detection

### 🚧 In Progress
- Servo hardware testing (awaiting parts)
- NeoPixel animations on Pico 2
- 3D printed head assembly

### 📋 Planned (v2.1+)
- Voice integration (Whisper/Piper)
- Face recognition (Tim vs strangers)
- Proactive behaviors
- Expression intensity levels

---

## Links

- **Main Gary System**: [Private repo]
- **Expressions Guide**: [docs/EXPRESSIONS_GUIDE.md](docs/EXPRESSIONS_GUIDE.md)
- **Hardware Guide**: [hardware/SHOPPING_LIST.md](hardware/SHOPPING_LIST.md)

---

<div align="center">

**GairiHead v2.0** - Dry wit. Smooth moves. Rainbow celebrations.

*"That's a terrible plan. I'm in."*

</div>
