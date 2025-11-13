# Session 2025-11-12: Stage Actions Metadata Implementation

**Date**: 2025-11-12
**Status**: ✅ Complete - All Quick Wins Implemented
**Feature**: Physical actions from Gary's response metadata (winks, LED patterns, pauses, sound effects)

---

## Overview

GairiHead now processes **stage action metadata** from Gary's LLM responses to trigger physical actions:
- 😉 **Winks & blinks** (eyelid servos)
- 💡 **LED emotion patterns** (eye rings)
- ⏸️ **Dramatic pauses** (timing delays)
- 🔊 **Sound effects** (sighs, gasps, laughs, etc.)

Gary strips action markers from response text and sends them as separate metadata fields.

---

## Gary Team: Response Format

### Required Response Format

Gary should now return responses with **emotion** and **actions** metadata:

```json
{
  "response": "Well, that's not good.",
  "emotion": "concerned",
  "actions": ["pause:1000", "sighs"]
}
```

**Note**: `response` text should be **clean** (no asterisk markers like `*sighs*`). Gary strips markers and converts them to the `actions` array.

### Supported Action Types

#### 1. Physical Actions (Eyelid Servos)
```json
"actions": ["wink"]      // Right eye winks for 150ms
"actions": ["blink"]     // Both eyes blink for 100ms
```

#### 2. LED Emotion Patterns (Eye Rings)
```json
"actions": ["chuckle"]        // Soft green, smile animation (amused expression)
"actions": ["excited"]        // Gold, rainbow animation (celebration expression)
"actions": ["eyes_light_up"]  // Bright white flash (surprised expression)
```

**Mapping**:
- `chuckle` → `amused` expression
- `excited` → `celebration` expression
- `eyes_light_up` → `surprised` expression

#### 3. Pauses (Timing Delays)
```json
"actions": ["pause:500"]        // 500ms pause
"actions": ["pause:1000"]       // 1 second dramatic pause
"actions": ["dramatic_pause"]   // Alias for pause
"actions": ["brief_pause"]      // Alias for pause
```

Duration can be specified with `:milliseconds` format.

#### 4. Sound Effects (Audio Playback)
```json
"actions": ["sigh"]      // Play sigh.wav
"actions": ["gasp"]      // Play gasp.wav
"actions": ["laugh"]     // Play laugh.wav
"actions": ["chuckle"]   // Play chuckle.wav (also triggers LED)
"actions": ["breath"]    // Play breath.wav
"actions": ["groan"]     // Play groan.wav
"actions": ["yawn"]      // Play yawn.wav
"actions": ["snicker"]   // Play snicker.wav
```

**Plural forms supported**: `sighs`, `gasps`, `laughs`, etc. (normalized automatically)

**Note**: Sound files must be placed in `/home/tim/GairiHead/sounds/` as `.wav` or `.mp3` files. See `sounds/README.md` for download sources.

#### 5. Future Actions (Not Yet Implemented)
```json
"actions": ["nod"]         // Requires head tilt servo (not installed)
"actions": ["shake_head"]  // Requires head pan servo (not installed)
```

These log warnings but don't error.

---

## Example Responses

### 1. Sarcastic Wink with Chuckle
```json
{
  "response": "Oh, that's brilliant.",
  "emotion": "sarcasm",
  "actions": ["wink", "chuckle"]
}
```
**Result**: GairiHead winks right eye, sets LEDs to amused pattern (soft green), plays chuckle sound (if available)

### 2. Surprised Gasp
```json
{
  "response": "You did WHAT?",
  "emotion": "surprised",
  "actions": ["gasp", "eyes_light_up"]
}
```
**Result**: Eyes flash bright white with expand pulse animation, plays gasp sound

### 3. Thoughtful Pause
```json
{
  "response": "Let me think about that. No.",
  "emotion": "deadpan",
  "actions": ["pause:1000", "blink"]
}
```
**Result**: 1 second pause before speaking, subtle blink

### 4. Tired Sigh
```json
{
  "response": "Alright, here's what we'll do.",
  "emotion": "thinking",
  "actions": ["sighs", "pause:500"]
}
```
**Result**: Plays sigh sound, 500ms pause

### 5. Multiple Emotions (List Format)
```json
{
  "response": "That's... interesting.",
  "emotion": ["skeptical", "intrigued"],
  "actions": ["pause:800"]
}
```
**Result**: Uses first emotion (`skeptical`) for voice/expression, 800ms dramatic pause

---

## Implementation Details

### Architecture

**File Structure**:
```
src/stage_actions.py       # New module - processes action metadata
main.py                    # Integration point - calls stage_actions after setting emotion
sounds/                    # Sound effect files (.wav/.mp3)
sounds/README.md           # Documentation for sound effect requirements
config/expressions.yaml    # Emotion → LED/servo mappings (unchanged)
```

### Processing Flow

```
Gary sends response
    ↓
main.py receives: {"response": "...", "emotion": "X", "actions": [...]}
    ↓
1. Set emotion expression (LEDs + eyelids)
    ↓
2. Process actions metadata (stage_actions.process_actions_metadata())
    ↓
    ├─→ Wink/blink → Servo animations
    ├─→ LED patterns → Expression changes
    ├─→ Pauses → asyncio.sleep()
    └─→ Sound effects → Audio playback
    ↓
3. Speak response text (TTS with emotion voice modulation)
```

**Location**: `main.py:451-456`

```python
# Process stage actions from Gary's metadata (winks, LED patterns, pauses, sounds)
if self.stage_actions and result.get('actions'):
    try:
        await self.stage_actions.process_actions_metadata(result['actions'])
    except Exception as e:
        logger.error(f"Failed to process stage actions: {e}")
```

### StageActionHandler API

**Initialization** (main.py):
```python
self.stage_actions = StageActionHandler(
    servo_controller=self.servos,
    expression_engine=self.expression_engine
)
```

**Main Methods**:
```python
async def process_actions_metadata(actions: List[Any]) -> None
    """Process list of actions from Gary's response"""

async def execute_action(action: str, params: Optional[Dict] = None) -> bool
    """Execute single action (wink, pause:500, chuckle, etc.)"""
```

**Internal Implementation Methods**:
```python
async def _action_wink() -> bool           # Quick Win #1
async def _action_blink() -> bool
async def _action_led_pattern(pattern_name: str) -> bool  # Quick Win #2
async def _action_pause(duration_ms: int) -> bool         # Quick Win #3
def _action_sound_effect(sound_name: str) -> bool         # Quick Win #4
```

---

## Quick Wins Implemented

| Priority | Action | Time Estimate | Status | Hardware |
|----------|--------|---------------|--------|----------|
| #1 | Wink/blink triggers | 5 min | ✅ Complete | Eyelid servos |
| #2 | LED emotion patterns | 30 min | ✅ Complete | Eye LED rings |
| #3 | Pause insertion | 1 hour | ✅ Complete | Software timing |
| #4 | Sound effects | 30 min | ✅ Complete* | Speaker (*needs .wav files) |
| #5 | Eyes light up | 20 min | ✅ Complete | Eye LED rings |

**Total Implementation**: ~2.5 hours ✅

---

## Sound Effects Setup

### Current Status
- ✅ Sound effect system implemented
- ⏳ Waiting for `.wav`/`.mp3` files to be added to `sounds/` directory
- 📁 0 sound files currently loaded

### Required Files

Place in `/home/tim/GairiHead/sounds/`:

**High Priority**:
- `sigh.wav` - For sighs
- `chuckle.wav` - For chuckle/chuckles
- `laugh.wav` - For laughs/laughing
- `breath.wav` - For takes a breath

**Medium Priority**:
- `gasp.wav` - For gasps
- `groan.wav` - For groans
- `yawn.wav` - For yawns
- `snicker.wav` - For snicker/snickers

### Format Requirements
- **Format**: WAV (preferred) or MP3
- **Sample Rate**: 16kHz or 44.1kHz (auto-converted)
- **Channels**: Mono preferred (stereo auto-converted)
- **Duration**: 0.5-2 seconds
- **Volume**: Auto-normalized

### Download Sources (Free)
- [Freesound.org](https://freesound.org) - CC0/CC-BY sounds
- [Zapsplat.com](https://zapsplat.com) - Free sound effects
- [BBC Sound Effects](http://bbcsfx.acropolis.org.uk/) - Public domain

### Testing
```bash
python -m src.stage_actions
```

---

## Testing Examples

### Test from Gary Side

Send this to test each action type:

```python
import json
import websockets

async def test_stage_actions():
    ws = await websockets.connect("ws://100.103.67.41:8765/ws")

    # Test wink + chuckle
    test_message = {
        'audio': base64_audio_data,
        'source': 'gairihead',
        'process_full_pipeline': True,
        'authorization': {'level': 1, 'user': 'tim', 'confidence': 0.95}
    }

    await ws.send(json.dumps(test_message))
    response = json.loads(await ws.recv())

    # Response should include actions
    assert 'actions' in response
    # Response text should NOT include *markers*
    assert '*' not in response['response']
```

### Test from GairiHead Side

```bash
cd /home/tim/GairiHead
python -m src.stage_actions
```

This runs test scenarios with mock action metadata.

---

## Changes Made

### New Files
- `src/stage_actions.py` - Stage action metadata processor (268 lines)
- `sounds/README.md` - Sound effect requirements documentation
- `docs/SESSION_2025-11-12_STAGE_ACTIONS.md` - This document

### Modified Files
- `main.py:185-189` - Initialize StageActionHandler with servo/expression controllers
- `main.py:451-456` - Process actions metadata before speaking
- `config/expressions.yaml` - No changes (already has amused, celebration, surprised)

### Dependencies
- `asyncio` - Already in stdlib
- `sounddevice` - Already installed (for TTS)
- `soundfile` - Already installed (for TTS)
- `numpy` - Already installed

---

## Future Enhancements

### Mid-Speech Timing (Advanced)
Currently all actions execute **before** speech. For better timing:

1. Parse action timing from markers
2. Insert pauses directly into TTS audio
3. Trigger winks/blinks at specific word boundaries
4. Sync LED patterns with speech cadence

**Example**:
```json
{
  "response": "Well, that's not good.",
  "emotion": "concerned",
  "actions": [
    {"type": "pause", "duration": 500, "after_word": 0},  // Pause before "Well"
    {"type": "sigh", "after_word": 1}                     // Sigh after "Well,"
  ]
}
```

### Additional Hardware Actions
- Head nod (requires tilt servo)
- Head shake (requires pan servo)
- Eye dart/look around (LED ring rotation effects)

### Sound Effect Variations
- Multiple variations per emotion (random selection)
- Volume modulation based on emotion intensity
- Pitch shifting for characterization

---

## Notes for Gary Team

1. **Clean Text**: Remove all `*markers*` from response text before sending
2. **Action Array**: Include as separate `actions` field
3. **Action Format**: Can be strings (`"wink"`) or dicts (`{"type": "pause", "duration": 500}`)
4. **Order Matters**: Actions execute in array order (pause first, then sound, then wink, etc.)
5. **Error Handling**: Invalid actions log warnings but don't crash
6. **Missing Hardware**: If servos/LEDs unavailable, logs warning and continues
7. **Sound Files**: System works without sound files (just skips playback)

---

## Testing Checklist

- [x] Wink action (right eye closes/opens)
- [x] Blink action (both eyes close/open)
- [x] LED patterns (chuckle, excited, eyes_light_up)
- [x] Pause timing (500ms, 1000ms delays)
- [x] Sound effect system (ready for .wav files)
- [x] Integration with main.py speak flow
- [x] Error handling (graceful degradation)
- [x] Multiple actions in sequence
- [ ] Sound playback (needs .wav files in sounds/)
- [ ] Physical hardware test (winks/blinks with actual servos)

---

## Session Summary

Successfully implemented stage actions metadata processing system with all 5 quick wins:

✅ **Winks & Blinks** - Eyelid servo animations
✅ **LED Patterns** - Emotion-based eye ring effects
✅ **Pauses** - Timing delays for dramatic effect
✅ **Sound Effects** - Audio playback system (needs .wav files)
✅ **Eyes Light Up** - Surprise/excitement LED flash

**Total Time**: ~2.5 hours
**Lines Added**: ~350 lines across 3 files
**Breaking Changes**: None (backwards compatible)

Gary can now send rich, expressive responses with physical actions that make GairiHead more lifelike and engaging!
