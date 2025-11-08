# GairiHead Team Requirements - Server-Side Processing

**Date**: 2025-11-08
**Status**: Gary server ready, GairiHead client needs updates
**Architecture**: Gary does ALL processing (transcription + LLM + training logging)

---

## What Gary Server Does (COMPLETE ✅)

1. ✅ **Receives audio** via websocket (base64 WAV)
2. ✅ **Transcribes locally** with faster-whisper (no API costs)
3. ✅ **Routes to tiered LLM**:
   - Simple queries → Qwen local (free)
   - Complex queries → Haiku (paid)
   - Strangers → Qwen only (security)
4. ✅ **Logs all interactions** for training data (Level 1 users only)
5. ✅ **Returns JSON** with transcription + response + tier used
6. ✅ **Keeps Qwen loaded** for 30 minutes (fast responses)

---

## What GairiHead Team Needs to Implement

### 1. Fix Face Recognition Bug 🔴 HIGH PRIORITY

**Current Issue**:
```python
ERROR | Face recognition error: VisionHandler.recognize_face()
       missing 1 required positional argument: 'face_rect'
```

**Location**: `~/gairihead/main.py` (or wherever `get_authorization()` is called)

**Fix Required**:
```python
# WRONG (current):
result = vision_handler.recognize_face()  # Missing face_rect

# CORRECT:
frame = camera_manager.read_frame()
faces = vision_handler.detect_faces(frame)

if faces:
    result = vision_handler.recognize_face(frame, faces[0])
    # Use result to build authorization
else:
    # No face detected = stranger
    authorization = {
        'level': 3,
        'user': 'unknown',
        'confidence': 0.0
    }
```

**Why Critical**: Currently defaulting to Level 1 even when face detection fails, giving strangers full access.

---

### 2. Send Correct Message Format to Gary 🔴 HIGH PRIORITY

**Current**: Unknown (need to verify what's being sent)

**Required Message Format**:
```python
import json
import base64
import websocket

# Build message
message = {
    'audio': base64_encoded_wav_data,          # Base64 WAV audio
    'source': 'gairihead',                      # Source identifier
    'process_full_pipeline': True,              # True = transcribe + LLM, False = transcribe only
    'authorization': {                          # From face recognition
        'level': 1,        # 1=Tim, 2=guest, 3=stranger
        'user': 'tim',     # User name or 'unknown'
        'confidence': 0.95 # Face recognition confidence
    }
}

# Send to Gary
ws = websocket.create_connection('ws://100.106.44.11:8765/ws')
ws.send(json.dumps(message))
response = ws.recv()
ws.close()
```

**Gary's Response Format**:
```python
response_json = json.loads(response)

# Full pipeline response (process_full_pipeline=True):
{
    'transcription': 'What is the weather today?',
    'response': 'Currently 45°F and partly cloudy...',
    'tier': 'cloud'  # or 'local'
}

# Transcription only (process_full_pipeline=False):
'What is the weather today?'  # Plain text
```

---

### 3. Handle Gary's Response 🟡 MEDIUM PRIORITY

**Parse Response**:
```python
import json

try:
    result = json.loads(response)

    if 'error' in result:
        # Error from Gary
        print(f"Error: {result['error']}")
        return

    # Success - full pipeline
    transcription = result['transcription']
    llm_response = result['response']
    tier_used = result['tier']

    print(f"You said: {transcription}")
    print(f"Gary says: {llm_response}")
    print(f"Using: {tier_used} model")

    # Speak the response
    tts_engine.say(llm_response)

except json.JSONDecodeError:
    # Plain text response (transcription only mode)
    transcription = response
    print(f"Transcription: {transcription}")
```

---

### 4. Update Voice Pipeline Flow 🟡 MEDIUM PRIORITY

**Old Flow** (Pi does transcription):
```
Record audio → Transcribe on Pi → Send text to Gary → Get response
```

**New Flow** (Gary does everything):
```
Record audio → Send to Gary → Get transcription + response → Speak
```

**Code Changes Needed**:

In `src/voice_handler.py` or `src/llm_tier_manager.py`:

```python
# OLD (remove local transcription):
# audio = record_audio()
# text = whisper.transcribe(audio)  # ← REMOVE THIS
# response = llm_manager.query(text)

# NEW (send audio to Gary):
audio = record_audio()
wav_bytes = audio_to_wav_bytes(audio)
audio_b64 = base64.b64encode(wav_bytes).decode('utf-8')

# Send to Gary with full pipeline
result = send_to_gary_full_pipeline(audio_b64, authorization)

# Result already has transcription + response
print(f"Transcription: {result['transcription']}")
speak(result['response'])
```

---

### 5. Update Expression Handling 🟢 LOW PRIORITY

**Current**: Expressions change during voice flow (listening → thinking → speaking)

**Recommended**:
- `idle` → User presses Enter
- `listening` → Recording audio
- `thinking` → Waiting for Gary's response
- `speaking` → Speaking Gary's response
- `idle` → Done

**Also set expression based on tier**:
```python
if result['tier'] == 'local':
    # Quick local response
    expression_engine.set_expression('happy')
elif result['tier'] == 'cloud':
    # Had to escalate to cloud
    expression_engine.set_expression('thinking')
```

---

## Testing Checklist for GairiHead Team

### Phase 1: Basic Communication ✅
- [ ] Send test audio to Gary websocket
- [ ] Verify Gary returns JSON with transcription
- [ ] Verify Gary returns response text
- [ ] Verify tier is 'local' or 'cloud'

### Phase 2: Face Recognition 🔴
- [ ] Fix face recognition error
- [ ] Test with Tim's face → Level 1
- [ ] Test with no face → Level 3
- [ ] Verify authorization sent to Gary matches detected level

### Phase 3: Voice Interaction 🟡
- [ ] Record → Send → Receive → Speak (full cycle)
- [ ] Test simple query (should use local Qwen)
- [ ] Test complex query (should use cloud Haiku)
- [ ] Test weather query (should call weather_forecast tool)

### Phase 4: Training Data 📝
- [ ] Verify interactions appear in `/Gary/data/gairihead_training_logs/`
- [ ] Verify response text is captured (not null)
- [ ] Verify tools_called is populated when tools used

---

## Current Issues to Debug

### Issue 1: Response Text Not Captured in Training Logs ✅ FIXED
**Status**: Fixed on Gary server (2025-11-08 14:47 CST)
**What was wrong**: Training logger wasn't detecting model type correctly, set responses to null
**Fix**: Always save response text regardless of model detection
**Action**: Test again with new Gary version

### Issue 2: Weather Query Didn't Call Weather Tool ⏳ PENDING
**Query**: "What is the weather today?"
**Expected**: Gary calls `weather_forecast` tool
**Actual**: Gary gave confused response without calling tool
**Need**: Full response text from Gary to diagnose (should be in training logs after fix)
**Action**: GairiHead team run another weather test and share full response

### Issue 3: 33k+ Tokens for Simple Query ⚠️ CONCERNING
**Query**: "Thanks for watching!"
**Expected**: ~100-500 tokens
**Actual**: 33,246 tokens (HUGE!)
**Cost**: $0.027 per query (should be <$0.001)
**Possible causes**:
- System prompt too long
- Tool descriptions included unnecessarily
- Haiku being verbose
- Multiple tool calls failing and retrying

**Action**: Need to see full response text to diagnose

---

## Gary Server Configuration

**Websocket Endpoint**: `ws://100.106.44.11:8765/ws`
**Ollama Keep-Alive**: 30 minutes
**Local Model**: qwen2.5:14b-instruct-q5_k_m (8.9GB)
**Cloud Model**: Claude Haiku 4.5
**Training Logs**: `/Gary/data/gairihead_training_logs/YYYY-MM-DD.jsonl`
**Response Time**: <1s local, <3s cloud (after first load)

---

## Questions for GairiHead Team

1. **Face Recognition**: Can you share the code where `get_authorization()` calls `recognize_face()`?

2. **Message Format**: What does your current websocket message look like? (The JSON you're sending to Gary)

3. **Full Response**: Can you run another test and share the COMPLETE response Gary gives (not just the first 50 chars)?

4. **Voice Flow**: Where in your code does audio recording → Gary sending → response handling happen?

5. **Timeline**: When can you implement the fixes and run full end-to-end tests?

---

## Summary

**Gary Side**: ✅ Ready for testing (all processing, training logging, tiered LLM working)

**GairiHead Side**: ⏳ Needs implementation
1. Fix face recognition bug
2. Send correct message format to Gary
3. Handle JSON response from Gary
4. Remove local transcription code
5. Test end-to-end voice pipeline

**Next Session**: After GairiHead team implements fixes, we'll debug the weather tool issue and excessive token usage.
