# GairiHead Expressions Guide

**Version**: 2.0
**Date**: 2025-11-07
**Total Expressions**: 24 (up from 12)

Complete guide to GairiHead's emotional expressions and personality features.

---

## Quick Reference

### Core States (Always Available)
- `idle` - Default calm monitoring
- `listening` - Actively receiving input
- `thinking` - Processing simple queries
- `processing` - Deep computation (cloud escalation)
- `alert` - Important information detected

### Positive Emotions
- `happy` - Obvious joy, wide smile
- `amused` - Subtle enjoyment, gentle humor
- `pride` - Satisfaction in work well done
- `celebration` - Victory, achievement (rainbow eyes!)

### Negative/Concerned
- `concerned` - Detected problem or frustration
- `frustrated` - System error or confusion
- `confused` - Uncertain, needs clarification
- `error` - Critical system failure
- `sheepish` - Oops, minor mistake

### TARS Personality (Dry Humor)
- `sarcasm` - Delivering witty response (may wink!)
- `deadpan` - Flat delivery of humor
- `unimpressed` - Not buying it, skeptical
- `disapproval` - Doubting your plan
- `bored` - Waiting, unengaged

### Intellectual States
- `calculating` - Rapid computation, tool selection
- `intrigued` - Curious, attention caught
- `skeptical` - Questioning, doubtful
- `deep_focus` - Intense concentration

### Special
- `welcome` - Tim detected, warm greeting
- `surprised` - Unexpected event
- `sleeping` - Low power idle state
- `diagnostic` - System self-test mode

---

## Detailed Expression Reference

### idle
**Use when**: Default state, monitoring environment
**Eyes**: Soft blue, gentle pulse
**Eyelids**: 45° (neutral, relaxed)
**Mouth**: 10° (slight smile)
**Blink rate**: 8s (natural)

**Transitions well to**: listening, thinking, alert, concerned

**Example**:
```python
engine.set_expression('idle')
```

---

### listening
**Use when**: User is speaking, wake word detected
**Eyes**: Cyan, solid (attentive)
**Eyelids**: 80° (wide open, engaged)
**Mouth**: 15° (slightly open)
**Blink rate**: 0 (no blink while listening)

**Special**: Auto-set when `start_listening()` called

**Example**:
```python
engine.start_listening()  # Sets to listening automatically
# User speaks...
engine.stop_listening()   # Returns to appropriate idle state
```

---

### sarcasm ⭐ TARS Signature
**Use when**: Delivering dry humor, witty comeback
**Eyes**: Amber, side-eye animation (one ring dimmer)
**Eyelids**: 25° left, 50° right (asymmetric squint)
**Mouth**: 8° (asymmetric smirk)
**Blink rate**: 5s

**Personality quirk**: 15% chance to wink after this expression!

**Example**:
```python
# Respond with sarcasm
engine.set_expression('sarcasm')
# Might wink right eye 0.5s later (automatic!)
time.sleep(2)
engine.return_to_idle()  # May drift to 'amused' or 'deadpan'
```

---

### deadpan ⭐ TARS Signature
**Use when**: Flat delivery of humor, no emotion shown
**Eyes**: Neutral gray-blue, solid
**Eyelids**: 42° (perfectly even, robotic precision)
**Mouth**: 5° (absolutely flat)
**Blink rate**: 9s (mechanical regularity)

**Perfect for**: "That's a terrible plan. I'm in."

**Example**:
```python
engine.set_expression('deadpan')
# Deliver dry observation with zero emotion
```

---

### unimpressed
**Use when**: User's idea is questionable, not convinced
**Eyes**: Dull gray, solid (low interest)
**Eyelids**: 40° (half-lidded boredom)
**Mouth**: 2° (minimal expression)
**Blink rate**: 10s (slow, uninterested)

**Example**:
```python
# User: "I'm going to reorganize the warehouse myself"
engine.set_expression('unimpressed')
# Response: "Excellent. I'll alert the chiropractor."
```

---

### calculating
**Use when**: Rapid computation, selecting tools, analyzing data
**Eyes**: Bright cyan, rapid chase animation
**Eyelids**: 35° (focused narrow)
**Mouth**: 5° (thoughtful)
**Blink rate**: 1.5s (quick, focused)

**Use before**: Calling expensive tools, complex analysis

**Example**:
```python
engine.set_expression('calculating')
# Perform tool selection logic...
# Then move to 'processing' if escalating to cloud
```

---

### processing
**Use when**: Deep computation, escalating to full Gary (Haiku tier)
**Eyes**: Purple, spinner animation (loading indicator)
**Eyelids**: 20° (very focused)
**Mouth**: 3° (concentration)
**Blink rate**: 2s (faster thinking blinks)

**Visual cue**: Purple = cloud processing (vs local)

**Example**:
```python
# Local LLM determined query is complex
engine.set_expression('processing')
# Escalate to Haiku tier...
# Return with answer
engine.set_expression('pride')  # Subtle satisfaction
```

---

### celebration 🎉
**Use when**: Task completed successfully, good news, victory
**Eyes**: RAINBOW color cycle, maximum brightness
**Eyelids**: 75° (wide, excited)
**Mouth**: 45° (huge grin)
**Blink rate**: 2s (excited)

**Special mode**: Can use `celebration_mode(duration=3.0)` for timed celebration

**Example**:
```python
# User: "We hit our sales goal!"
engine.celebration_mode(duration=5.0)  # 5 seconds of rainbow joy
# Automatically returns to idle after
```

---

### micro_reaction()
**Use for**: Quick subtle reactions without full expression change
**Duration**: 300ms flash
**Types**: `surprise`, `disapproval`, `interest`, `skeptical`

**Example**:
```python
# Currently in 'listening' state
# User says something unexpected
engine.micro_reaction('surprise')  # Brief wide-eye flash
# Returns to 'listening' automatically

# Or show subtle interest
engine.micro_reaction('interest')  # One eye slightly wider
```

---

## Personality Quirks (Autonomous)

### Wink After Sarcasm
**Probability**: 15%
**Timing**: 0.5s after sarcasm expression set
**Eye**: Right

Adds emphasis to dry humor delivery. Pure TARS.

### Sigh When Idle
**Probability**: 5% per update
**Behavior**: Eyelids droop briefly, then return
**Effect**: Subtle boredom indicator

### Random Micro-Expressions
**Probability**: 2% per update
**Types**: Interest, skeptical, disapproval
**Purpose**: Liveliness when not actively engaged

---

## Mood Drift (Contextual Memory)

GairiHead remembers the last 3 expressions and may "drift" back to related moods when returning to idle.

**Mood relationships**:
```
sarcasm → amused, deadpan, unimpressed
happy → amused, pride, celebration
frustrated → concerned, skeptical, bored
alert → intrigued, surprised, concerned
thinking → processing, calculating, deep_focus
```

**Example flow**:
```python
# User interaction
engine.set_expression('sarcasm')    # Quirk: might wink
# ... deliver response ...
engine.return_to_idle()  # Instead of 'idle', drifts to 'amused' (30% chance)

# Later
engine.return_to_idle()  # Might drift back to 'deadpan' (remembers sarcasm)
```

---

## Special Methods

### Servo-Only Reactions

**Wink** (sarcasm emphasis):
```python
controller.wink('right', duration=0.25)  # Classic right-eye wink
controller.wink('left')                  # Left-eye wink
```

**Eyebrow Raise** (surprise, skepticism):
```python
controller.eyebrow_raise('left', height=15)   # One eyebrow
controller.eyebrow_raise('both', height=10)   # Both eyebrows
```

**Double Take** (surprise reaction):
```python
controller.double_take()  # Quick look away and snap back
```

**Sigh** (boredom, frustration):
```python
engine.sigh()  # Eyelids droop, brief pause, return
```

---

## Demo Mode

Test all expressions in sequence:

```python
engine.demo_mode()
```

**Cycles through**:
1. Core states (idle, listening, thinking...)
2. Positive emotions (happy, amused, pride...)
3. TARS personality (sarcasm, deadpan, unimpressed...)
4. Reactions (alert, surprised, confused...)

**Duration**: ~45 seconds total
**Use**: Hardware testing, showing off to visitors

---

## Animation Reference

### NeoPixel Eye Animations

**Static/Subtle**:
- `solid` - No animation, static color
- `pulse` - Gentle brightness fade
- `slow_pulse` - Very gradual (calm states)
- `breathe` - Deep sine wave (sleeping)

**Active/Thinking**:
- `chase` - Pixels rotate around ring
- `rapid_chase` - Fast rotation (calculating)
- `spinner` - Single bright pixel (loading)

**Attention**:
- `flash` - Quick on/off (alert)
- `alternate_flash` - Rings flash alternately
- `error_pulse` - SOS morse pattern

**Special**:
- `rainbow` - RGB color cycle (celebration)
- `sparkle` - Random pixels twinkle
- `theater_chase` - Running lights effect
- `comet` - Bright pixel with trail

**Personality**:
- `smile` - Bottom pixels brighter (happy)
- `narrow` - Top pixels brighter (eyebrow raise)
- `side_eye` - One ring dimmer (sarcasm)

---

## Best Practices

### Expression Selection

**For responses**:
1. Match emotion to content:
   - Good news → `happy` or `amused`
   - Warning → `alert` or `concerned`
   - Data analysis → `calculating` → `processing`
   - Dry humor → `sarcasm` or `deadpan`

2. Consider context:
   - First interaction of day → `welcome`
   - Repeated question → `bored` or `unimpressed`
   - After success → `pride` (subtle) or `celebration` (major)

3. Use micro-reactions for subtlety:
   - Brief surprise without full expression change
   - Acknowledge without interrupting

### Timing

**Fast transitions** (instant):
- Error states
- Alert/surprised reactions
- Micro-expressions

**Smooth transitions** (0.3s default):
- Most emotional changes
- Return to idle
- Mood drifts

**Slow transitions** (0.5-1s):
- Sleep mode entry
- Celebration → idle

### State Management

**Always use**:
```python
engine.start_listening()   # Not set_expression('listening')
engine.start_speaking()    # Manages state properly
engine.thinking()          # Better than direct set_expression
```

**Let engine manage**:
- Automatic blinking (varies naturally)
- Return to idle (uses mood drift)
- Personality quirks (winks, sighs)

---

## Common Patterns

### Query Response Flow
```python
# User asks question
engine.start_listening()

# Analyze query
engine.set_expression('calculating')

# If complex
engine.set_expression('processing')  # Visual: purple = cloud

# Deliver answer
engine.start_speaking()  # Eyes stay open, mouth moves

# After answer
engine.stop_speaking()   # Drifts to appropriate idle state
```

### Sarcastic Response
```python
engine.set_expression('sarcasm')
# Might wink automatically (15% chance)
speak("That's a bold strategy. Let's see how that works out.")
time.sleep(2)
engine.set_expression('deadpan')  # Or let it drift to 'amused'
```

### Error Handling
```python
try:
    # Attempt operation
    engine.set_expression('processing')
    result = risky_operation()
    engine.set_expression('pride')  # Success!
except Exception as e:
    engine.set_expression('error')  # Red SOS pattern
    engine.set_expression('sheepish')  # Apologetic
```

### Celebration
```python
# Major achievement
engine.celebration_mode(duration=5.0)  # Rainbow party!

# Minor win
engine.set_expression('pride')  # Subtle satisfaction
engine.micro_reaction('interest')  # Brief pleased reaction
```

---

## Troubleshooting

### Expression doesn't change
- Check if expression name is in `expressions.yaml`
- Verify servo/NeoPixel controllers attached
- Check for active speaking/listening state (blocks some changes)

### Quirks not triggering
- Verify `personality_quirks_enabled = True`
- Check probabilities (intentionally rare for naturalness)
- Ensure servo_controller is attached

### Mood drift too frequent/rare
- Adjust `mood_persistence` (default 0.3 = 30%)
- Modify `mood_map` to add/remove relationships

### Transitions too fast/slow
- Set `smooth=False` for instant movement
- Adjust `duration` parameter in set_eyelid/set_mouth calls

---

## Future Enhancements (When Hardware Arrives)

### With Servos
- Full expression testing
- Fine-tune eyelid/mouth angles
- Calibrate smooth movement speeds
- Test all personality quirks

### With NeoPixels
- Implement all 18 animations on Pico
- Sync eye animations with expressions
- Test eyebrow raise effect (top pixel brightness)
- Rainbow celebration mode

### With Voice
- Mouth amplitude sync with speech
- Emphasis word micro-blinks
- Pause detection
- Voice tone affects expression intensity

---

## Quick Command Reference

```python
# Core
engine.set_expression('idle')
engine.return_to_idle()

# State
engine.start_listening()
engine.start_speaking()
engine.thinking(level='deep')

# Reactions
engine.react('surprised')  # 2s flash, auto-return
engine.micro_reaction('disapproval')  # 0.3s flash

# Special
engine.celebration_mode(duration=3.0)
engine.demo_mode()
engine.check_time_of_day_mood()

# Servo-only
controller.wink('right')
controller.eyebrow_raise('left', height=15)
controller.double_take()
controller.micro_expression('surprise', duration=0.3)

# Personality
engine.sigh()  # Autonomous boredom
# Winks happen automatically after sarcasm (15% chance)
```

---

## Expression Count

**Total**: 24 expressions
**Core states**: 5
**Emotions**: 12
**TARS personality**: 5
**Special modes**: 4
**Animations**: 18

**Plus**:
- 4 micro-expression types
- Mood drift system
- 3 autonomous personality quirks
- Contextual memory (3 expression history)

---

**Status**: ✅ Software complete, awaiting servo/NeoPixel hardware
**Version**: 2.0 (2025-11-07)
**Character**: TARS-like - dry, witty, competent, caring underneath

This is GairiHead's soul. Use it well.
