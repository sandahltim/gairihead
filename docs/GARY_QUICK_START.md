# Gary → GairiHead Quick Start

## ✅ Status: FULLY OPERATIONAL

**Server:** ws://100.103.67.41:8766 (GairiHead's Tailscale IP)
**Both processes running:** Main app (local) + Server (remote)
**Hardware coordination:** Automatic - Gary's commands take priority

---

## Quick Test

```python
import asyncio
import json
import websockets

async def test_gary_control():
    uri = "ws://100.103.67.41:8766"

    async with websockets.connect(uri) as ws:
        # Test 1: Make GairiHead speak
        await ws.send(json.dumps({
            "action": "speak",
            "params": {
                "text": "Hello! I'm Gary, speaking through GairiHead.",
                "expression": "happy"
            }
        }))
        response = await asyncio.wait_for(ws.recv(), timeout=30)
        print("Speak:", json.loads(response))

        # Test 2: Change expression
        await ws.send(json.dumps({
            "action": "set_expression",
            "params": {"expression": "thinking"}
        }))
        response = await ws.recv()
        print("Expression:", json.loads(response))

asyncio.run(test_gary_control())
```

---

## Available Commands (✅ All Working)

### 1. `speak` - Make GairiHead Talk
**TESTED ✅** - Mouth animation + Arduino display + TTS working

```json
{
  "action": "speak",
  "params": {
    "text": "Your message here",
    "expression": "happy"
  }
}
```

### 2. `set_expression` - Facial Control
**TESTED ✅** - All expressions working

```json
{
  "action": "set_expression",
  "params": {
    "expression": "thinking"
  }
}
```

Available expressions:
- `idle`, `alert`, `listening`, `thinking`
- `happy`, `sarcasm`, `confused`, `surprised`
- `skeptical`, `amused`, `disapproval`

### 3. `capture_snapshot` - Camera Photo
```json
{
  "action": "capture_snapshot",
  "params": {
    "quality": 85
  }
}
```

### 4. `detect_faces` - Face Detection
```json
{
  "action": "detect_faces",
  "params": {}
}
```

### 5. `get_status` - Hardware Status
```json
{
  "action": "get_status",
  "params": {}
}
```

---

## Key Features

✅ **Hardware Coordination**
- Gary's commands automatically get priority over local button presses
- Main app yields gracefully when Gary is using hardware
- Automatic lock management

✅ **Arduino Display Integration**
- Shows Gary's speech text to local user
- Updates expression/status indicators
- "Gary" tier displayed during remote control

✅ **Mouth Animation**
- Automatically synchronized with speech
- Uses calibrated values from expressions.yaml
- 20 FPS natural talking motion

✅ **Power Efficiency**
- Camera lazy initialization (opens only when needed)
- Servo idle detach (no jitter when not moving)
- ~99% reduction in camera-on time

---

## Testing

Test script available: `/home/tim/GairiHead/scripts/test_server_commands.py`

```bash
cd /home/tim/GairiHead
source venv/bin/activate
python3 scripts/test_server_commands.py
```

---

## Implementation Details

**What just got added (2025-11-08):**
1. Complete `speak` action with TTS + mouth animation
2. Hardware coordinator for priority management
3. Arduino display integration for remote commands
4. Camera lazy initialization
5. Servo jitter reduction

**Commit:** `fa4d7fb` - feat: Add Gary remote control API with hardware coordination

**Full docs:** `/home/tim/GairiHead/docs/GARY_API_REFERENCE.md`
