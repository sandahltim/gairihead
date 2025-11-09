# Gary → GairiHead Integration Quick Start

**Last Updated**: 2025-11-09
**Status**: ✅ Server verified working

---

## Connection Details

**WebSocket Server:**
- Host: `ws://100.103.67.41:8766` (Tailscale)
- Port: `8766`
- Protocol: WebSocket with JSON messages

**Authentication Token:**
```
av-UQ9Eh64ZcbRPadshCzpqiVkG5Rw2QxDTuJYRU__o
```

---

## Connection Flow

### Step 1: Connect to WebSocket
```python
import websockets
import json

ws = await websockets.connect("ws://100.103.67.41:8766")
```

### Step 2: Authenticate (FIRST MESSAGE!)
```python
# MUST be the first message sent
auth_msg = {"token": "av-UQ9Eh64ZcbRPadshCzpqiVkG5Rw2QxDTuJYRU__o"}
await ws.send(json.dumps(auth_msg))

# Wait for confirmation
response = json.loads(await ws.recv())
# Expected: {"status": "authenticated", "message": "Authentication successful"}
```

### Step 3: Send Commands
```python
# Now you can send commands
command = {
    "action": "speak",
    "params": {
        "text": "Hello from Gary!",
        "expression": "happy",
        "animate_mouth": True
    }
}
await ws.send(json.dumps(command))
response = json.loads(await ws.recv())
```

---

## Available Commands

### 1. `speak` - Text-to-Speech with Mouth Animation
**Most commonly used command for Gary**

```python
{
    "action": "speak",
    "params": {
        "text": "The text to speak",           # Required, max 5000 chars
        "expression": "happy",                 # Optional, sets facial expression
        "animate_mouth": True                  # Optional, default True
    }
}
```

**Mouth Animation:**
- ✅ **Handled locally by GairiHead** (audio-reactive)
- Automatically syncs mouth movement with speech audio
- Uses amplitude detection from TTS audio stream
- Sensitivity and max_angle defined in `expressions.yaml` under "speaking" expression

**Response:**
```python
{"status": "success", "message": "Speech completed"}
# or
{"status": "error", "error": "Error message"}
```

---

### 2. `set_expression` - Change Facial Expression
```python
{
    "action": "set_expression",
    "params": {
        "expression": "alert"    # Required, max 50 chars
    }
}
```

**Available Expressions:** (24 total)
- Basic: `idle`, `listening`, `thinking`, `alert`, `happy`, `sleeping`
- Emotions: `sarcasm`, `skeptical`, `frustrated`, `concerned`, `surprised`, `amused`
- States: `speaking`, `processing`, `calculating`, `bored`, `confused`, `intrigued`
- Reactions: `welcome`, `unimpressed`, `disapproval`, `deadpan`, `pride`, `celebration`
- Error: `error`

---

### 3. `capture_snapshot` - Take Photo
```python
{
    "action": "capture_snapshot",
    "params": {
        "quality": 90    # Optional, 1-100, default 85
    }
}
```

**Response:**
```python
{
    "status": "success",
    "image": "base64_encoded_jpeg_data",
    "width": 640,
    "height": 480
}
```

---

### 4. `analyze_scene` - Capture + Face Detection
```python
{
    "action": "analyze_scene",
    "params": {
        "quality": 90    # Optional
    }
}
```

**Response:**
```python
{
    "status": "success",
    "image": "base64_image",
    "faces_detected": 2,
    "face_locations": [[top, right, bottom, left], ...],
    "face_encodings": [...],  # For recognition
    "known_persons": ["Tim", "Unknown"]
}
```

---

### 5. `record_audio` - Record Microphone
```python
{
    "action": "record_audio",
    "params": {
        "duration": 5.0    # Optional, 0.1-60 seconds, default 5
    }
}
```

**Response:**
```python
{
    "status": "success",
    "audio": "base64_encoded_wav_data",
    "duration": 5.2,
    "sample_rate": 16000
}
```

---

### 6. `detect_faces` - Fast Face Detection Only
```python
{
    "action": "detect_faces",
    "params": {}
}
```

**Response:**
```python
{
    "status": "success",
    "faces_detected": 1,
    "face_locations": [[top, right, bottom, left]]
}
```

---

### 7. `get_status` - System Status
```python
{
    "action": "get_status",
    "params": {}
}
```

**Response:**
```python
{
    "status": "success",
    "camera": "available",
    "servos": "available",
    "arduino": "connected",
    "expression": "idle"
}
```

---

### 8. `blink` - Trigger Blink Animation
```python
{
    "action": "blink",
    "params": {}
}
```

---

### 9. `test_sync` - Test Synchronized Eye Movement
```python
{
    "action": "test_sync",
    "params": {}
}
```

---

## Common Mistakes

### ❌ Wrong: Sending command before authentication
```python
# This will FAIL
ws = await websockets.connect("ws://100.103.67.41:8766")
await ws.send(json.dumps({"action": "speak", "params": {...}}))
# Server will close connection
```

### ✅ Correct: Authenticate first
```python
ws = await websockets.connect("ws://100.103.67.41:8766")
await ws.send(json.dumps({"token": "av-UQ9Eh64ZcbRPadshCzpqiVkG5Rw2QxDTuJYRU__o"}))
auth = await ws.recv()  # Wait for auth confirmation
# NOW send commands
await ws.send(json.dumps({"action": "speak", "params": {...}}))
```

---

### ❌ Wrong: Using wrong parameter names
```python
# Common variable naming mistakes:
{
    "action": "speak",
    "params": {
        "message": "Hello"        # WRONG - should be "text"
    }
}

{
    "action": "speak",
    "params": {
        "text": "Hello",
        "animate": True           # WRONG - should be "animate_mouth"
    }
}
```

### ✅ Correct: Use exact parameter names
```python
{
    "action": "speak",
    "params": {
        "text": "Hello",              # ✓ Correct
        "expression": "happy",        # ✓ Optional
        "animate_mouth": True         # ✓ Optional
    }
}
```

---

## Error Handling

### Authentication Errors
```python
# Invalid token
{"status": "error", "error": "Authentication failed: Invalid token"}

# Timeout (no auth within 5 seconds)
# Connection will be closed by server
```

### Command Errors
```python
# Unknown action
{
    "status": "error",
    "error": "Unknown action: invalid_cmd. Allowed: analyze_scene, blink, ..."
}

# Missing required parameter
{
    "status": "error",
    "error": "Missing required parameter 'text' for speak action"
}

# Invalid parameter value
{
    "status": "error",
    "error": "Parameter 'text' exceeds maximum length (5000 characters)"
}

# Hardware busy
{
    "status": "error",
    "error": "Hardware busy - could not acquire lock"
}
```

---

## Complete Python Example

```python
import asyncio
import json
import websockets

async def gary_control_gairihead():
    # Connect
    ws = await websockets.connect("ws://100.103.67.41:8766")

    try:
        # STEP 1: Authenticate
        await ws.send(json.dumps({
            "token": "av-UQ9Eh64ZcbRPadshCzpqiVkG5Rw2QxDTuJYRU__o"
        }))

        auth = json.loads(await ws.recv())
        if auth.get("status") != "authenticated":
            raise Exception(f"Auth failed: {auth}")

        print("✅ Authenticated")

        # STEP 2: Make GairiHead speak
        await ws.send(json.dumps({
            "action": "speak",
            "params": {
                "text": "Hello! I am GairiHead, Gary's physical presence.",
                "expression": "welcome",
                "animate_mouth": True
            }
        }))

        response = json.loads(await ws.recv())
        print(f"Speak result: {response}")

        # STEP 3: Take a photo
        await ws.send(json.dumps({
            "action": "capture_snapshot",
            "params": {"quality": 90}
        }))

        photo = json.loads(await ws.recv())
        if photo.get("status") == "success":
            print(f"Photo captured: {len(photo['image'])} bytes")

        # STEP 4: Analyze scene
        await ws.send(json.dumps({
            "action": "analyze_scene",
            "params": {}
        }))

        scene = json.loads(await ws.recv())
        print(f"Faces detected: {scene.get('faces_detected', 0)}")

    finally:
        await ws.close()

# Run
asyncio.run(gary_control_gairihead())
```

---

## Diagnostic Tests

To verify GairiHead server is working:

```bash
cd ~/GairiHead
source venv/bin/activate
python test_websocket_auth.py
```

Expected: 3-4 tests pass (Test 3 may show different behavior but is acceptable)

---

## Current Server Status

**Date Verified**: 2025-11-09 15:20

✅ Server running on port 8766
✅ Authentication working
✅ All commands tested and working
✅ Input validation enabled
✅ Mouth animation handled locally (audio-reactive)
✅ Expression system working (24 expressions)
✅ Camera, servos, Arduino display all functional

**Server PID**: 105317 (started 14:51)

---

## Support

If you encounter issues:

1. **Check server is running:**
   ```bash
   sudo lsof -i :8766
   ```

2. **Check server logs:**
   ```bash
   tail -f ~/GairiHead/logs/gairi_head.log
   ```

3. **Restart server:**
   ```bash
   cd ~/GairiHead
   pkill -f gairi_head_server
   source venv/bin/activate
   export GAIRIHEAD_API_TOKEN="av-UQ9Eh64ZcbRPadshCzpqiVkG5Rw2QxDTuJYRU__o"
   python src/gairi_head_server.py
   ```

---

**For Gary Team**: All systems verified working. The most common issue is variable naming - make sure to use exact parameter names as documented above.
