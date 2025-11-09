# 🔴 URGENT: Gary Team - Fix Your Connection Code

**Issue Identified**: You're using **HTTP POST** instead of **WebSocket**

---

## The Problem

Your code is trying to use HTTP POST requests (like a REST API):
```python
# This is what you're doing (WRONG)
requests.post("http://100.103.67.41:8766", ...)
```

**GairiHead is a WebSocket server, not a REST API.** HTTP POST will never work.

---

## The Fix (3 Steps)

### 1. Install websockets library
```bash
pip install websockets
```

### 2. Change your code to use WebSocket

**Before (HTTP - WRONG):**
```python
import requests

response = requests.post(
    "http://100.103.67.41:8766",
    json={"action": "speak", "params": {"text": "Hello"}}
)
```

**After (WebSocket - CORRECT):**
```python
import asyncio
import json
import websockets

async def speak():
    # Connect with WebSocket
    ws = await websockets.connect("ws://100.103.67.41:8766")

    # Authenticate FIRST
    await ws.send(json.dumps({
        "token": "av-UQ9Eh64ZcbRPadshCzpqiVkG5Rw2QxDTuJYRU__o"
    }))
    await ws.recv()  # Wait for auth confirmation

    # Now send command
    await ws.send(json.dumps({
        "action": "speak",
        "params": {"text": "Hello", "animate_mouth": True}
    }))

    # Wait for response (speak takes 10-60 seconds!)
    response = await asyncio.wait_for(ws.recv(), timeout=120)
    print(response)

    await ws.close()

asyncio.run(speak())
```

### 3. Test your connection

```bash
cd ~/GairiHead
python test_gary_connection.py
```

This will test your connection and show you if it's working.

---

## Key Differences

| What You're Doing | What You Need To Do |
|-------------------|---------------------|
| `import requests` | `import websockets` |
| `http://...` | `ws://...` |
| `requests.post()` | `websockets.connect()` |
| One-shot request | Persistent connection |
| No authentication handshake | Must authenticate first |

---

## Documentation

- **Quick Start**: `docs/GARY_INTEGRATION_QUICKSTART.md`
- **Troubleshooting**: `docs/GARY_TROUBLESHOOTING.md`
- **Test Script**: `test_gary_connection.py`

---

## Why This Happened

WebSocket and HTTP are **completely different protocols**:

- **HTTP POST**: Send one request, get one response, connection closes
- **WebSocket**: Open persistent connection, send/receive multiple messages

GairiHead uses WebSocket because:
- Commands can take 60+ seconds (speaking long text)
- Need bidirectional communication
- Lower latency for real-time control

Your timeout errors were happening because you were trying to use the wrong protocol. The server was rejecting your HTTP POST requests immediately.

---

## Server Status: ✅ Working Perfectly

The GairiHead server is running correctly and accepting WebSocket connections. The issue is entirely on the client side (your code).

Server logs show:
```
ValueError: unsupported HTTP method; expected GET; got POST
```

This confirms you're using HTTP POST instead of WebSocket.

---

## Need Help?

1. Read `docs/GARY_TROUBLESHOOTING.md`
2. Run `python test_gary_connection.py`
3. Use the code example above
4. Make sure you're using `websockets` library (not `requests`)

**Bottom line**: Switch from `requests.post()` to `websockets.connect()` and your timeouts will disappear.
