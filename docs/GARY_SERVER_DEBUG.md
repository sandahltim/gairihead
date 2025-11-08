# Gary Server Debugging

## Current Issue (2025-11-08)

### Symptoms
Gary server is returning error responses with unknown tier/model:

```
Tier: unknown | Model: unknown
Transcription: "This is a test to see if Gary recognizes that this is Tim."
Response: "I apologize, but I'm having trouble processing you..."
```

### What's Happening

1. **GairiHead sends**: Audio + authorization (level 3, unknown user)
2. **Gary receives**: Full pipeline request
3. **Gary responds**: Error message instead of proper response
4. **Missing fields**: `tier` and `model` not in response JSON

### Expected Behavior

Gary should return JSON with:
```json
{
  "transcription": "...",
  "response": "...",
  "tier": "local|cloud",
  "model": "llama3.2:3b|haiku|sonnet"
}
```

### Current Behavior

Gary returning:
```json
{
  "transcription": "...",
  "response": "I apologize, but I'm having trouble processing you..."
  // Missing: tier, model
}
```

---

## Possible Causes on Gary Server

### 1. Tier Selection Logic Issue
- Gary may not be determining tier properly
- Falling back to error response
- Check Gary's tier manager logs

### 2. LLM Processing Failure
- Llama/Haiku/Sonnet may be failing
- Gary catching exception and returning generic error
- Check Gary's LLM processing logs

### 3. Authorization Level Issue
- Level 3 (stranger) may trigger different behavior
- Gary may be refusing to process for strangers
- Check Gary's authorization handling

### 4. Response Format Issue
- Gary may not be setting tier/model in response
- Old response format without metadata
- Check Gary's response construction code

---

## Gary Server Checks

### Check 1: Gary Logs
Look for errors in Gary's console/logs when processing request:
```bash
# On Gary server
tail -f /path/to/gary/logs
# or
journalctl -u gary -f
```

### Check 2: Test Direct Gary Connection
Test Gary's WebSocket directly:
```python
import websocket
import json
import base64

ws = websocket.create_connection("ws://100.106.44.11:8765/ws")

# Send test audio query
message = {
    "audio": "<base64 audio>",
    "source": "test",
    "process_full_pipeline": True,
    "tier_preference": "auto",
    "authorization": {
        "level": 1,  # Try level 1 (Tim)
        "user": "tim",
        "confidence": 1.0
    }
}

ws.send(json.dumps(message))
response = ws.recv()
print(response)
ws.close()
```

### Check 3: Test with Level 1 Auth
Face recognition is working now (fixed path), so next test should show:
- Authorization: Level 1 (Tim)
- User: tim
- Confidence: >0.6

Gary might process Level 1 requests differently than Level 3 (stranger).

### Check 4: Check Gary's Tier Manager
Ensure Gary's tier manager is:
1. Receiving full pipeline request correctly
2. Determining tier (local vs cloud)
3. Processing with appropriate model
4. Returning tier/model in response

---

## GairiHead Side - Already Fixed

✅ **Logging**: Now shows tier and model from Gary response
✅ **Handling**: Gracefully handles missing tier/model (shows "unknown")
✅ **Face Recognition**: Fixed path to known_faces directory
✅ **Button Debouncing**: Added cooldown to prevent loop

---

## Next Steps

1. **Test with face recognition working**:
   - Run GairiHead
   - Stand in front of camera
   - Should now recognize Tim (Level 1)
   - See if Gary responds differently to Level 1

2. **Check Gary server logs**:
   - Look for errors when processing request
   - Verify tier selection logic
   - Verify LLM processing

3. **Debug Gary's response construction**:
   - Ensure tier/model fields are added to JSON response
   - Check if authorization level affects processing

4. **Test different authorization levels**:
   - Level 1 (Tim) - full access
   - Level 2 (Guest) - limited access
   - Level 3 (Stranger) - minimal access

---

## Error Message Analysis

Gary's error: "I apologize, but I'm having trouble processing you..."

This is likely a catch-all error response when:
- LLM fails to generate response
- Tier selection fails
- Authorization check fails
- Some other processing error occurs

**Action**: Check Gary server code for where this error message is generated and what conditions trigger it.
