# Gary → GairiHead API Reference

## Setup

**To enable Gary remote control:**
```bash
cd /home/tim/GairiHead
./scripts/start_remote_mode.sh
```

This stops the main app and runs server-only mode so Gary has exclusive access to hardware.

**To return to local button-press mode:**
```bash
./scripts/start_gairihead.sh
```

---

## WebSocket Connection

**Server URL:** `ws://100.103.67.41:8766`

**Message Format:**
```json
{
  "action": "command_name",
  "params": {
    "param1": "value1",
    "param2": "value2"
  }
}
```

---

## Available Commands

### 1. `speak` - Make GairiHead Talk

**Purpose:** Text-to-speech with automatic mouth animation

**Parameters:**
- `text` (required): Text to speak
- `expression` (optional): Facial expression during speech (default: current expression)
- `animate_mouth` (optional): Enable mouth animation (default: true)

**Example:**
```json
{
  "action": "speak",
  "params": {
    "text": "Hello! I'm Gary speaking through GairiHead.",
    "expression": "happy"
  }
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "text": "Hello! I'm Gary speaking through GairiHead.",
    "expression": "happy",
    "animated_mouth": true,
    "timestamp": 1762659000.123
  }
}
```

**Note:** This command takes time (several seconds for TTS synthesis + playback). WebSocket may timeout if keep-alive is too short.

---

### 2. `set_expression` - Control Facial Servos

**Purpose:** Change GairiHead's facial expression

**Parameters:**
- `expression` (required): Expression name from expressions.yaml

**Available Expressions:**
- `idle` - Neutral resting face
- `alert` - Eyes wide, attentive
- `listening` - Slightly open eyes, receptive
- `thinking` - Eyes narrowed, contemplative
- `happy` - Wide eyes, open mouth
- `sarcasm` - Asymmetric eyes, slight smirk
- `confused` - Asymmetric questioning look
- `surprised` - Very wide eyes and mouth
- `skeptical` - Narrowed eyes, doubt
- `amused` - Playful expression
- `disapproval` - Narrowed eyes, closed mouth

**Example:**
```json
{
  "action": "set_expression",
  "params": {
    "expression": "thinking"
  }
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "expression": "thinking",
    "timestamp": 1762659000.123
  }
}
```

---

### 3. `capture_snapshot` - Get Camera Image

**Purpose:** Capture single frame from camera

**Parameters:**
- `quality` (optional): JPEG quality 1-100 (default: 85)

**Example:**
```json
{
  "action": "capture_snapshot",
  "params": {
    "quality": 90
  }
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "image": "base64_encoded_jpeg_data...",
    "format": "jpeg",
    "width": 640,
    "height": 480,
    "timestamp": 1762659000.123
  }
}
```

---

### 4. `record_audio` - Record Microphone

**Purpose:** Record audio from USB microphone

**Parameters:**
- `duration` (optional): Recording duration in seconds (default: 3)
- `sample_rate` (optional): Sample rate in Hz (default: 16000)

**Example:**
```json
{
  "action": "record_audio",
  "params": {
    "duration": 5,
    "sample_rate": 16000
  }
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "audio": "base64_encoded_wav_data...",
    "format": "wav",
    "duration": 5,
    "sample_rate": 16000,
    "timestamp": 1762659000.123
  }
}
```

---

### 5. `analyze_scene` - Camera + Face Detection

**Purpose:** Capture frame and detect faces

**Example:**
```json
{
  "action": "analyze_scene",
  "params": {}
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "image": "base64_encoded_jpeg_data...",
    "format": "jpeg",
    "faces_detected": 1,
    "face_locations": [
      {"x": 120, "y": 80, "w": 200, "h": 200}
    ],
    "timestamp": 1762659000.123
  }
}
```

---

### 6. `detect_faces` - Fast Face Detection

**Purpose:** Detect faces without returning full image (faster)

**Example:**
```json
{
  "action": "detect_faces",
  "params": {}
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "faces_detected": 1,
    "face_locations": [
      {"x": 120, "y": 80, "w": 200, "h": 200}
    ],
    "timestamp": 1762659000.123
  }
}
```

---

### 7. `get_status` - Check Hardware Status

**Purpose:** Get current system status

**Example:**
```json
{
  "action": "get_status",
  "params": {}
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "expression": "idle",
    "camera_available": true,
    "servos_available": true,
    "server_uptime": 1762659000.123,
    "timestamp": 1762659000.123,
    "note": "Hardware may be in use by main app"
  }
}
```

---

## Error Responses

All commands return errors in this format:

```json
{
  "status": "error",
  "error": "Error message describing what went wrong"
}
```

**Common errors:**
- `"Servos currently in use by main app"` - Main app is running, use remote mode
- `"Failed to capture frame"` - Camera not available
- `"No text provided to speak"` - Missing required parameter
- `"Unknown action: xyz"` - Invalid command name

---

## Usage Examples

### Python Example
```python
import asyncio
import json
import websockets

async def control_gairihead():
    uri = "ws://100.103.67.41:8766"

    async with websockets.connect(uri) as ws:
        # Make GairiHead speak
        command = {
            "action": "speak",
            "params": {
                "text": "Hello from Gary!",
                "expression": "happy"
            }
        }
        await ws.send(json.dumps(command))
        response = await asyncio.wait_for(ws.recv(), timeout=30)  # Long timeout for TTS
        print(json.loads(response))

        # Change expression
        command = {
            "action": "set_expression",
            "params": {"expression": "thinking"}
        }
        await ws.send(json.dumps(command))
        response = await ws.recv()
        print(json.loads(response))

asyncio.run(control_gairihead())
```

---

## Notes

1. **Timeout Considerations:** The `speak` command can take 10-30 seconds depending on text length. Set WebSocket timeouts accordingly.

2. **Hardware Conflicts:** Only ONE process can control servos at a time. Use remote mode when Gary needs control.

3. **Camera Access:** Camera uses lazy initialization - it opens when needed and closes after to allow sharing between processes.

4. **Expression Persistence:** Expressions persist until changed. No automatic reset.

5. **Mouth Animation:** Automatically synchronized with speech when using `speak` command. Uses calibrated values from expressions.yaml.
