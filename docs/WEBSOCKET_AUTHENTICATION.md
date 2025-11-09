# WebSocket Authentication Guide

**Updated**: 2025-11-09
**Version**: 1.0 - Token-based authentication

---

## Overview

The GairiHead WebSocket server now requires authentication for all connections. This prevents unauthorized access to hardware controls (camera, servos, microphone).

**Security Features:**
- ✅ Token-based authentication
- ✅ Input validation on all commands
- ✅ Parameter type and range checking
- ✅ Action whitelist (only allowed commands)
- ⏸️ Rate limiting (future enhancement)

---

## Quick Start

### 1. Your API Token

Your current API token is:
```
av-UQ9Eh64ZcbRPadshCzpqiVkG5Rw2QxDTuJYRU__o
```

**⚠️ Keep this token secret!** Anyone with this token can control your GairiHead hardware.

### 2. How Authentication Works

1. Client connects to `ws://100.103.67.41:8766`
2. Client sends auth message as **first message**:
   ```json
   {"token": "av-UQ9Eh64ZcbRPadshCzpqiVkG5Rw2QxDTuJYRU__o"}
   ```
3. Server validates token and responds:
   ```json
   {"status": "authenticated", "message": "Authentication successful"}
   ```
4. Client can now send commands

**If authentication fails:**
- Server responds with error
- Connection is closed
- Client must reconnect and try again

---

## Configuration

### Method 1: Environment Variable (RECOMMENDED)

**Most secure** - token not stored in files

```bash
# Set in your shell
export GAIRIHEAD_API_TOKEN="av-UQ9Eh64ZcbRPadshCzpqiVkG5Rw2QxDTuJYRU__o"

# Or create .env file (NOT committed to git)
echo 'GAIRIHEAD_API_TOKEN=av-UQ9Eh64ZcbRPadshCzpqiVkG5Rw2QxDTuJYRU__o' > .env

# Start server (reads from environment)
python src/gairi_head_server.py
```

### Method 2: Config File

**Convenient** - but token is in a file

Already configured in `config/gairi_head.yaml`:
```yaml
server:
  api_token: "av-UQ9Eh64ZcbRPadshCzpqiVkG5Rw2QxDTuJYRU__o"
  host: "0.0.0.0"
  port: 8766
```

**Note**: Environment variable takes precedence over config file.

---

## Client Examples

### Python (asyncio)

```python
import asyncio
import json
import websockets

async def connect_to_gairihead():
    uri = "ws://100.103.67.41:8766"
    token = "av-UQ9Eh64ZcbRPadshCzpqiVkG5Rw2QxDTuJYRU__o"

    async with websockets.connect(uri) as ws:
        # Step 1: Authenticate
        await ws.send(json.dumps({"token": token}))
        auth_response = json.loads(await ws.recv())

        if auth_response["status"] != "authenticated":
            raise Exception(f"Auth failed: {auth_response}")

        print("✅ Authenticated!")

        # Step 2: Send commands
        await ws.send(json.dumps({
            "action": "speak",
            "params": {"text": "Hello from Gary!"}
        }))

        response = json.loads(await ws.recv())
        print(f"Response: {response}")

asyncio.run(connect_to_gairihead())
```

### Python (synchronous)

```python
import json
from websocket import create_connection

ws = create_connection("ws://100.103.67.41:8766")

# Authenticate
ws.send(json.dumps({"token": "av-UQ9Eh64ZcbRPadshCzpqiVkG5Rw2QxDTuJYRU__o"}))
auth = json.loads(ws.recv())
print(f"Auth: {auth}")

# Send command
ws.send(json.dumps({"action": "get_status", "params": {}}))
status = json.loads(ws.recv())
print(f"Status: {status}")

ws.close()
```

### JavaScript (Node.js)

```javascript
const WebSocket = require('ws');

const ws = new WebSocket('ws://100.103.67.41:8766');
const token = 'av-UQ9Eh64ZcbRPadshCzpqiVkG5Rw2QxDTuJYRU__o';

ws.on('open', () => {
    // Authenticate first
    ws.send(JSON.stringify({ token: token }));
});

ws.on('message', (data) => {
    const response = JSON.parse(data);

    if (response.status === 'authenticated') {
        console.log('✅ Authenticated!');

        // Send command
        ws.send(JSON.stringify({
            action: 'get_status',
            params: {}
        }));
    } else {
        console.log('Response:', response);
    }
});
```

---

## Allowed Commands (Whitelist)

Only these actions are accepted:

1. `capture_snapshot` - Capture camera frame
2. `record_audio` - Record microphone audio
3. `analyze_scene` - Capture + face detection
4. `get_status` - Get system status
5. `set_expression` - Change facial expression
6. `detect_faces` - Fast face detection
7. `speak` - Text-to-speech
8. `blink` - Trigger blink animation
9. `test_sync` - Test synchronized eye movement

**Any other action will be rejected.**

---

## Input Validation

All parameters are validated before execution:

### speak
- `text` (required): string, max 5000 characters
- `expression` (optional): string, max 50 characters

### set_expression
- `expression` (required): string, max 50 characters

### record_audio
- `duration` (optional): number, 0.1-60 seconds

### capture_snapshot
- `quality` (optional): integer, 1-100

**Invalid parameters will be rejected with a clear error message.**

---

## Error Handling

### Authentication Errors

```json
// Invalid token
{
    "status": "error",
    "error": "Authentication failed: Invalid token"
}

// Invalid auth message format
{
    "status": "error",
    "error": "Authentication failed: Invalid auth message"
}

// Timeout (no auth within 5 seconds)
// Connection closed by server
```

### Validation Errors

```json
// Unknown action
{
    "status": "error",
    "error": "Unknown action: invalid_cmd. Allowed: analyze_scene, blink, ..."
}

// Missing required parameter
{
    "status": "error",
    "error": "Missing required parameter 'text' for speak action"
}

// Invalid parameter type
{
    "status": "error",
    "error": "Parameter 'duration' must be a number"
}

// Out of range
{
    "status": "error",
    "error": "Parameter 'quality' must be between 1 and 100"
}
```

---

## Testing Authentication

### Run the test script:

```bash
cd ~/GairiHead
source venv/bin/activate

# Make sure server is running first
python src/gairi_head_server.py &

# Run tests
python test_websocket_auth.py
```

**Expected output:**
```
Test 1: Valid authentication...
  ✅ Authentication successful
  ✅ Command executed successfully

Test 2: Invalid authentication (should fail)...
  ✅ Correctly rejected invalid token

Test 3: No authentication (should timeout/fail)...
  ✅ Connection timed out (expected)

Test 4: Input validation...
  ✅ Invalid action rejected
  ✅ Invalid parameter rejected

✅ All tests passed! Authentication is working correctly.
```

---

## Updating Gary Client

Your Gary server needs to be updated to send the auth token. Update the Gary WebSocket client code:

```python
# In Gary's gairi_head_tool or connection code
async def connect_to_gairihead():
    ws = await websockets.connect("ws://100.103.67.41:8766")

    # NEW: Send authentication first
    await ws.send(json.dumps({
        "token": "av-UQ9Eh64ZcbRPadshCzpqiVkG5Rw2QxDTuJYRU__o"
    }))

    # Wait for auth confirmation
    auth_response = json.loads(await ws.recv())
    if auth_response.get("status") != "authenticated":
        raise Exception(f"GairiHead auth failed: {auth_response}")

    # Now send your actual command
    await ws.send(json.dumps({
        "action": "capture_snapshot",
        "params": {"quality": 90}
    }))

    return await ws.recv()
```

---

## Generating New Tokens

If you need to generate a new token (e.g., if compromised):

```bash
# Generate secure random token
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Update in config file or environment variable
# Restart server for changes to take effect
```

---

## Security Best Practices

1. **Never commit the token to git**
   - ✅ `.env` is in `.gitignore`
   - ⚠️ Config file IS committed (consider using env var instead)

2. **Use environment variables in production**
   ```bash
   export GAIRIHEAD_API_TOKEN="your-token"
   ```

3. **Rotate tokens periodically**
   - Generate new token every 90 days
   - Update all clients

4. **Restrict network access**
   - Use Tailscale for remote access
   - Or bind to `127.0.0.1` for localhost only
   - Or configure firewall rules

5. **Monitor authentication logs**
   ```bash
   grep "Authentication failed" logs/gairi_head.log
   ```

---

## Troubleshooting

### "Authentication failed: Invalid token"
- Check token spelling (copy-paste recommended)
- Check for extra spaces or newlines
- Verify server is using correct token

### "Connection closed immediately"
- You sent invalid auth message
- Check JSON format
- Must send auth as **first message**

### "Connection timeout"
- Server expects auth within 5 seconds
- Send auth immediately after connecting

### Commands fail after authentication
- Check if action is in allowed list
- Verify parameter types and ranges
- Check server logs for details

---

## Files Created/Modified

- ✅ `config/gairi_head.yaml` - Added server section with token
- ✅ `.env.example` - Template for environment variables
- ✅ `.gitignore` - Added .env to prevent token leaks
- ✅ `test_websocket_auth.py` - Test script
- ✅ `src/gairi_head_server.py` - Authentication implementation

---

**Security Status**: ✅ Production-ready with token authentication

**Next Steps**:
1. Update Gary client to send auth token
2. Test end-to-end with Gary integration
3. Monitor logs for failed auth attempts

