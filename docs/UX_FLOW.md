# GairiHead UX Flow

## Improved User Experience Flow (2025-11-08)

### Production Mode Flow (Touchscreen Trigger)

**State 1: IDLE**
- Display: "Ready - Touch to start"
- Servos: Idle expression
- Eyes: Dim, slow breathing effect
- Action: Waiting for center button press

**State 2: SCANNING (Triggered by touchscreen press)**
- Display: "Scanning..." + alert expression icon
- Servos: Alert expression (eyes wide, looking at user)
- Eyes: Bright white (scanning mode)
- Action: Camera captures frame → Face recognition runs
- Duration: ~500ms

**State 3: AUTHORIZED**
- Display: Shows recognition result:
  - "Tim - Level 1" (Main User)
  - "Guest - Level 2"
  - "Unknown - Level 3" (Stranger)
- Servos: Brief acknowledgment (slight nod or blink)
- Action: Brief pause (500ms) to show result

**State 4: LISTENING**
- Display: "Listening..." + microphone icon
- Servos: Attentive expression
- Eyes: Pulsing blue (listening indicator)
- Action: **VAD recording starts** (auto-stops when you finish speaking)
- User Experience:
  - Start speaking when ready
  - Stop when done - system detects automatically
  - No awkward 3-second timeout!

**State 5: THINKING**
- Display: "Processing..." + thinking icon
- Servos: Thinking expression (eyes narrowed, processing)
- Eyes: Rotating colors (processing indicator)
- Action: Audio sent to Gary → Transcription + LLM processing

**State 6: SPEAKING**
- Display: Shows conversation:
  - User: "What's the weather?"
  - Gairi: "It's sunny and 72°F"
- Display also shows:
  - Tier used (local/cloud)
  - Model used (llama/haiku/sonnet)
  - Response time
- Servos: Speaking expression (mouth moves)
- Eyes: Green (speaking indicator)
- Action: TTS plays response with Piper voice

**State 7: COMPLETE → Return to IDLE**
- Display: Returns to "Ready - Touch to start"
- Servos: Return to idle expression
- Eyes: Return to dim breathing
- Action: Wait for next button press

---

## Key UX Improvements

### ✅ Before (Poor UX):
1. Press button
2. ❌ Face scan unclear - no visual feedback
3. ❌ "RECORDING NOW" but already started
4. ❌ Fixed 3-second timeout cuts you off or wastes time
5. ❌ No visibility into model/tier used
6. ❌ No clear state transitions

### ✅ After (Improved UX):
1. Press button → **IMMEDIATE visual feedback** ("Scanning...")
2. ✅ Face scan with clear state on display
3. ✅ Shows authorization result before listening
4. ✅ "Listening..." → **speak when ready, auto-stops when done**
5. ✅ Clear state transitions with visual/servo feedback
6. ✅ Shows which model responded (debug Haiku usage)
7. ✅ Natural conversation flow

---

## Visual Feedback Summary

| State | Arduino Display | Servos | Eyes | Duration |
|-------|----------------|--------|------|----------|
| Idle | "Ready - Touch to start" | Idle | Dim breathing | Until button press |
| Scanning | "Scanning..." | Alert | Bright white | ~500ms |
| Authorized | "Tim - Level 1" | Acknowledge | Normal | 500ms pause |
| Listening | "Listening..." | Attentive | Pulsing blue | Until user stops speaking |
| Thinking | "Processing..." | Thinking | Rotating colors | 1-3 seconds |
| Speaking | Conversation + stats | Speaking | Green | Duration of speech |

---

## Future Enhancements (Planned)

### Voice Authorization Fallback
**Use Case**: When camera can't identify user with certainty

**Flow**:
1. Face scan returns low confidence (<0.6)
2. GairiHead asks: "I don't recognize you. Please state your name."
3. User says name: "This is Tim"
4. Voice recognition confirms identity
5. Proceed with authorized session

**Benefits**:
- Works in low light
- Works if user wearing glasses/hat
- Backup authentication method
- More secure than camera-only

**Implementation**: After other bugs fixed

---

## Testing Checklist

- [ ] Press touchscreen → See "Scanning..." immediately
- [ ] Face detected → See "Tim - Level 1" (or appropriate level)
- [ ] See "Listening..." before recording starts
- [ ] Speak → Recording auto-stops when you stop talking
- [ ] See "Processing..." during LLM processing
- [ ] See conversation + model name on display
- [ ] See "Speaking..." during TTS playback
- [ ] Return to idle state after interaction
- [ ] Servos move during expression changes
- [ ] No JSON errors in logs
- [ ] Model name logged (verify not always Haiku)

---

## Core Principle Applied

**#8: Do it well, then do it fast**
- First get the UX flow right (clear states, visual feedback)
- Then optimize performance (VAD, single-call pipeline)
- Better to have slower but clear UX than fast but confusing
