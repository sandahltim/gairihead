# Gary Team - Troubleshooting Guide

**Last Updated**: 2025-11-09 15:30
**Current Issues Identified**: ✅ Root cause found

---

## 🔴 CRITICAL ISSUE: Using HTTP POST Instead of WebSocket

### What's Happening

The server logs show:
```
ValueError: unsupported HTTP method; expected GET; got POST
websockets.exceptions.InvalidMessage: did not receive a valid HTTP request
```

**This means you're trying to use HTTP requests (like REST API) instead of WebSocket connections.**

---

## ❌ WRONG: Using HTTP POST (like REST API)

```python
# THIS WILL NOT WORK
import requests

response = requests.post(
    "http://100.103.67.41:8766",  # Using http://
    json={
        "token": "...",
        "action": "speak",
        "params": {"text": "Hello"}
    }
)
```

```python
# THIS WILL ALSO NOT WORK
import httpx

async with httpx.AsyncClient() as client:
    response = await client.post(  # Using POST
        "ws://100.103.67.41:8766",
        json={"action": "speak", ...}
    )
```

**Why it fails:**
- GairiHead is a **WebSocket server**, not a REST API
- WebSocket requires persistent connection with handshake
- HTTP POST sends one-time requests
- Completely different protocols

---

## ✅ CORRECT: Using WebSocket Connection

### Option 1: Using `websockets` Library (Recommended)

```bash
pip install websockets
```

```python
import asyncio
import json
import websockets

async def control_gairihead():
    # Step 1: Connect using WebSocket (not HTTP)
    ws = await websockets.connect("ws://100.103.67.41:8766")

    try:
        # Step 2: Authenticate (FIRST MESSAGE)
        await ws.send(json.dumps({
            "token": "av-UQ9Eh64ZcbRPadshCzpqiVkG5Rw2QxDTuJYRU__o"
        }))

        auth = json.loads(await ws.recv())
        if auth.get("status") != "authenticated":
            raise Exception(f"Auth failed: {auth}")

        # Step 3: Send command
        await ws.send(json.dumps({
            "action": "speak",
            "params": {
                "text": "Hello from Gary!",
                "animate_mouth": True
            }
        }))

        # Step 4: Get response
        response = json.loads(await ws.recv())
        print(f"Result: {response}")

    finally:
        await ws.close()

# Run it
asyncio.run(control_gairihead())
```

---

### Option 2: Using `websocket-client` Library (Synchronous)

```bash
pip install websocket-client
```

```python
import json
from websocket import create_connection

# Connect
ws = create_connection("ws://100.103.67.41:8766")

# Authenticate
ws.send(json.dumps({
    "token": "av-UQ9Eh64ZcbRPadshCzpqiVkG5Rw2QxDTuJYRU__o"
}))

auth = json.loads(ws.recv())
print(f"Auth: {auth}")

# Send command
ws.send(json.dumps({
    "action": "speak",
    "params": {"text": "Hello!"}
}))

result = json.loads(ws.recv())
print(f"Result: {result}")

ws.close()
```

---

### Option 3: Using `socketio` (If You're Using Socket.IO)

**Note**: This is **not** Socket.IO, it's plain WebSocket. But if you must use socketio:

```python
import socketio

# This won't work directly - Socket.IO is different from WebSocket
# You need to use websockets library instead
```

---

## Key Differences: HTTP vs WebSocket

| Feature | HTTP POST (REST) | WebSocket |
|---------|-----------------|-----------|
| Connection | One request per connection | Persistent connection |
| Protocol | `http://` or `https://` | `ws://` or `wss://` |
| Handshake | No handshake | Requires handshake (GET upgrade) |
| Direction | Request → Response only | Bidirectional (send/receive both ways) |
| Library | `requests`, `httpx` | `websockets`, `websocket-client` |

**GairiHead uses WebSocket** because:
- Long-running operations (speaking takes 10-60 seconds)
- Real-time bidirectional communication
- Lower latency for commands
- Can send status updates back to Gary

---

## Timeout Errors - What They Mean

### 1. Authentication Timeout (5 seconds)
```
Connection closed by server after 5 seconds
```

**Cause**: You didn't send authentication token within 5 seconds of connecting

**Fix**: Send auth token immediately after connection:
```python
ws = await websockets.connect("ws://100.103.67.41:8766")
# Send auth RIGHT AWAY (don't wait)
await ws.send(json.dumps({"token": "..."}))
await ws.recv()  # Wait for confirmation
```

---

### 2. Command Timeout
```
TimeoutError after sending command
```

**Cause**: Some commands take time (especially `speak`)

**Fix**: Increase your receive timeout:
```python
# Wrong - default timeout too short
response = await ws.recv()  # Might timeout on long speech

# Right - set longer timeout for speak
response = await asyncio.wait_for(ws.recv(), timeout=120)  # 2 minutes
```

**Command Duration Estimates:**
- `get_status`: <100ms
- `set_expression`: ~200ms
- `capture_snapshot`: ~500ms
- `detect_faces`: ~1 second
- `analyze_scene`: ~2 seconds
- `record_audio`: 0.1-60 seconds (depends on duration param)
- **`speak`: 5-60 seconds** (depends on text length)

---

### 3. Hardware Lock Timeout
```json
{"status": "error", "error": "Hardware busy - could not acquire lock"}
```

**Cause**: Another command is using the hardware (camera, servos, etc.)

**Fix**: Wait and retry, or check if you have multiple connections fighting for hardware

---

## Testing Your Connection

### Quick Test Script

```python
import asyncio
import json
import websockets

async def test():
    print("Connecting...")
    ws = await websockets.connect("ws://100.103.67.41:8766")
    print("✅ Connected")

    print("Authenticating...")
    await ws.send(json.dumps({
        "token": "av-UQ9Eh64ZcbRPadshCzpqiVkG5Rw2QxDTuJYRU__o"
    }))
    auth = json.loads(await ws.recv())
    print(f"Auth response: {auth}")

    if auth.get("status") == "authenticated":
        print("✅ Authenticated successfully!")

        print("Testing get_status...")
        await ws.send(json.dumps({"action": "get_status", "params": {}}))
        status = json.loads(await ws.recv())
        print(f"Status: {status}")

        print("✅ All tests passed!")
    else:
        print(f"❌ Auth failed: {auth}")

    await ws.close()

asyncio.run(test())
```

**Expected output:**
```
Connecting...
✅ Connected
Authenticating...
Auth response: {'status': 'authenticated', 'message': 'Authentication successful'}
✅ Authenticated successfully!
Testing get_status...
Status: {'status': 'success', 'camera': 'available', ...}
✅ All tests passed!
```

---

## Common Gary Code Patterns That Need Fixing

### ❌ Pattern 1: Using requests library
```python
# WRONG
import requests
requests.post("http://100.103.67.41:8766", json={"action": "speak", ...})
```

**Fix**: Use websockets library instead

---

### ❌ Pattern 2: Using HTTP URL
```python
# WRONG
url = "http://100.103.67.41:8766"  # http://
```

**Fix**:
```python
url = "ws://100.103.67.41:8766"  # ws://
```

---

### ❌ Pattern 3: One-shot request style
```python
# WRONG - treating like REST API
for command in commands:
    ws = await websockets.connect("ws://...")
    await ws.send(command)
    await ws.recv()
    await ws.close()  # Reconnecting every time!
```

**Fix**: Keep connection open
```python
# RIGHT - reuse connection
ws = await websockets.connect("ws://...")
await ws.send(auth)
await ws.recv()

for command in commands:
    await ws.send(command)
    await ws.recv()

await ws.close()  # Close once at end
```

---

### ❌ Pattern 4: Not waiting for authentication
```python
# WRONG
ws = await websockets.connect("ws://...")
await ws.send(json.dumps({"action": "speak", ...}))  # Didn't auth first!
```

**Fix**:
```python
# RIGHT
ws = await websockets.connect("ws://...")
await ws.send(json.dumps({"token": "..."}))  # Auth first
await ws.recv()  # Wait for confirmation
await ws.send(json.dumps({"action": "speak", ...}))  # Now send command
```

---

## Integration into Gary's Tool System

### Example Tool Class

```python
import asyncio
import json
import websockets
from typing import Optional

class GairiHeadTool:
    def __init__(self):
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.host = "ws://100.103.67.41:8766"
        self.token = "av-UQ9Eh64ZcbRPadshCzpqiVkG5Rw2QxDTuJYRU__o"

    async def connect(self):
        """Establish WebSocket connection and authenticate"""
        if self.ws and not self.ws.closed:
            return  # Already connected

        self.ws = await websockets.connect(self.host)

        # Authenticate
        await self.ws.send(json.dumps({"token": self.token}))
        auth = json.loads(await self.ws.recv())

        if auth.get("status") != "authenticated":
            raise Exception(f"GairiHead auth failed: {auth}")

    async def speak(self, text: str, expression: str = None, animate_mouth: bool = True):
        """Make GairiHead speak"""
        await self.connect()

        await self.ws.send(json.dumps({
            "action": "speak",
            "params": {
                "text": text,
                "expression": expression,
                "animate_mouth": animate_mouth
            }
        }))

        # Wait up to 2 minutes for speech to complete
        response = await asyncio.wait_for(self.ws.recv(), timeout=120)
        return json.loads(response)

    async def capture_photo(self, quality: int = 90):
        """Capture photo from GairiHead camera"""
        await self.connect()

        await self.ws.send(json.dumps({
            "action": "capture_snapshot",
            "params": {"quality": quality}
        }))

        response = await asyncio.wait_for(self.ws.recv(), timeout=10)
        return json.loads(response)

    async def set_expression(self, expression: str):
        """Set facial expression"""
        await self.connect()

        await self.ws.send(json.dumps({
            "action": "set_expression",
            "params": {"expression": expression}
        }))

        response = await asyncio.wait_for(self.ws.recv(), timeout=5)
        return json.loads(response)

    async def close(self):
        """Close connection"""
        if self.ws and not self.ws.closed:
            await self.ws.close()

# Usage in Gary
gairihead = GairiHeadTool()
result = await gairihead.speak("Hello from Gary!")
photo = await gairihead.capture_photo()
await gairihead.close()
```

---

## Checklist for Gary Team

- [ ] Install `websockets` library: `pip install websockets`
- [ ] Change URL from `http://` to `ws://`
- [ ] Replace `requests.post()` or `httpx.post()` with `websockets.connect()`
- [ ] Send authentication token as FIRST message
- [ ] Wait for authentication confirmation before sending commands
- [ ] Keep connection open (don't reconnect for each command)
- [ ] Use appropriate timeouts (120 seconds for speak command)
- [ ] Test with the quick test script above

---

## Current Server Status

✅ Server running and accepting WebSocket connections
✅ Authentication working correctly
✅ All commands tested and functional
❌ **Cannot accept HTTP POST requests** - This is by design

**The server is working perfectly. The issue is on the client side - you need to use WebSocket protocol, not HTTP.**

---

## Need Help?

If still having issues after switching to WebSocket:

1. Run the test script above
2. Share the error output
3. Check if you're using `websockets` library (not `requests`)
4. Verify URL starts with `ws://` (not `http://`)

The most common mistake is using HTTP client libraries instead of WebSocket libraries.
