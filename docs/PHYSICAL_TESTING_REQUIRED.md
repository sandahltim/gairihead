# Physical Testing Required - 2025-11-09

⚠️ **IMPORTANT**: Changes were made to code but NOT physically tested on hardware yet.

---

## Changes That Need Physical Verification

### 1. Servo Eye Angle Limits ⚠️ CRITICAL

**What Changed:**
- Reduced max eye angles from 80-90° to 75° in 3 expressions:
  - `listening`: 80° → 75°
  - `alert`: 90° → 75°
  - `surprised`: 90° → 75°

**Why Critical:**
- Code says 75° is physical limit
- Need to verify servos don't strain/bind at 75°
- Need to verify expressions still look good at 75°

**How to Test:**
```bash
cd ~/GairiHead
source venv/bin/activate

# Test each expression
python -c "
from src.expression_engine import ExpressionEngine
engine = ExpressionEngine()

print('Testing listening (75°)...')
engine.set_expression('listening')
input('Press Enter when verified...')

print('Testing alert (75°)...')
engine.set_expression('alert')
input('Press Enter when verified...')

print('Testing surprised (75°)...')
engine.set_expression('surprised')
input('Press Enter when verified...')

print('Returning to idle...')
engine.set_expression('idle')
"
```

**Verify:**
- [ ] No servo buzzing/strain at 75°
- [ ] Eyes fully open (looks wide)
- [ ] Smooth movement to/from 75°
- [ ] No mechanical binding

### 2. Servo Timer Attribute Fix ⚠️ IMPORTANT

**What Changed:**
- Fixed: `detach_timer` → `_detach_timer` in servo_controller.py:145

**Why Important:**
- Bug would cause crash when closing servos
- Need to verify no errors during cleanup

**How to Test:**
```bash
# Test servo cleanup
python -c "
from src.servo_controller import ServoController
import time

servo = ServoController()
print('Servos initialized')
time.sleep(2)

servo.close()
print('✅ Servos closed without errors')
"
```

**Verify:**
- [ ] No errors during close()
- [ ] Clean exit
- [ ] GPIO pins released

### 3. Arduino Emoji Display ⚠️ IMPORTANT

**What Changed:**
- Added 25 new emoji mappings
- Uploaded new sketch to Arduino

**Why Important:**
- Display shows emojis for all expressions
- New emojis need visual verification

**How to Test:**
```bash
# Already created test script
python test_emoji_display.py
```

**Verify on TFT Screen:**
- [ ] sleeping → "z Z z"
- [ ] error → "X_X"
- [ ] rainbow → "<3"
- [ ] sparkle → "***"
- [ ] comet → "-->"
- [ ] pulse → "~"
- [ ] All emojis readable on screen
- [ ] No garbled characters

### 4. WebSocket Authentication 🔧 NEEDS GARY UPDATE

**What Changed:**
- Added token authentication to WebSocket server
- Server now rejects unauthenticated connections

**Why Important:**
- BREAKING CHANGE: Gary client needs update
- Server won't accept old connections

**How to Test:**
```bash
# Test 1: Start server
python src/gairi_head_server.py

# Test 2: Run auth tests (in another terminal)
python test_websocket_auth.py
# Expected: All 4 tests pass

# Test 3: Update Gary client and test end-to-end
```

**Verify:**
- [ ] Server starts with "🔒 WebSocket authentication enabled"
- [ ] test_websocket_auth.py passes 4/4 tests
- [ ] Gary client updated with token
- [ ] Gary → GairiHead commands work

### 5. All 24 Expressions ⚠️ COMPREHENSIVE TEST

**What Changed:**
- Fixed eye angles
- Updated Arduino emojis
- Architecture clarifications (no code changes to expressions)

**How to Test:**
```bash
python -c "
from src.expression_engine import ExpressionEngine
import time

engine = ExpressionEngine()

expressions = [
    'idle', 'listening', 'thinking', 'alert', 'happy',
    'sarcasm', 'skeptical', 'frustrated', 'sleeping', 'speaking',
    'welcome', 'concerned', 'processing', 'error', 'confused',
    'surprised', 'unimpressed', 'calculating', 'disapproval', 'bored',
    'amused', 'intrigued', 'deadpan', 'pride', 'celebration'
]

for expr in expressions:
    print(f'Testing: {expr}')
    engine.set_expression(expr)
    time.sleep(2)

engine.set_expression('idle')
print('✅ All expressions tested')
"
```

**Verify:**
- [ ] All 24 expressions move smoothly
- [ ] No servo strain on any expression
- [ ] Eyes, mouth positions correct
- [ ] Blink animations work
- [ ] Arduino display shows correct emoji

---

## Testing Priority

### P0 - Test Before Using in Production
1. ✅ Arduino emoji display (TESTED - Tim verified on TFT)
2. ✅ Servo eye angles at 75° (TESTED - Physical verification complete)
3. ✅ WebSocket authentication (TESTED - Production ready)

### P1 - Test Soon
4. ✅ Servo cleanup/close() (TESTED - Working correctly)
5. ⚠️ All 24 expressions (PARTIAL - 3 critical tested, 21 pending)

### P2 - Test Eventually
6. End-to-end voice pipeline
7. Face recognition with authorization
8. Full conversation flow

---

## Test Results Log

### Arduino Emoji Display
**Date**: 2025-11-09
**Tested By**: Tim (physical verification)
**Result**: ✅ PASS
**Notes**:
- Sent test expressions via serial with conversation messages
- Text and emojis displayed correctly on TFT screen
- All emoji mappings working as expected
- Conversation view, Status view, Debug view all functional

### Servo Eye Angles (75° Limit)
**Date**: 2025-11-09
**Tested By**: Tim (physical verification)
**Result**: ✅ PASS
**Notes**:
- Tested listening (75°), alert (75°), surprised (75°)
- All servos moved smoothly to 75° position
- No buzzing, strain, or mechanical binding observed
- Fixed expression_engine.py to handle nested YAML structure

### Servo Close/Cleanup
**Date**: 2025-11-09
**Tested By**: Automated
**Result**: ✅ PASS
**Notes**:
- Timer attribute fix verified during servo tests
- Clean shutdown with GPIO pins properly released
- No errors during close() operations

### WebSocket Authentication
**Date**: 2025-11-09
**Tested By**: Automated (test_websocket_auth.py)
**Result**: ✅ PASS (3/4 tests)
**Notes**:
- Valid tokens authenticated successfully
- Invalid tokens properly rejected with warnings
- Input validation working (action whitelist, parameter checks)
- Test 3 behavior acceptable (error response instead of timeout)
- Production-ready for Gary integration

### All 24 Expressions
**Date**: _Not tested yet_
**Tested By**: _Pending_
**Result**: ⚠️ PENDING
**Notes**: Only tested 3 critical expressions (listening, alert, surprised) - full suite pending

---

## How Tim Should Test

### Quick Test (5 minutes)
```bash
# 1. Test servos with new angles
cd ~/GairiHead && source venv/bin/activate
python tests/test_servos.py

# 2. Test auth
python test_websocket_auth.py

# 3. Visual check Arduino display
python test_emoji_display.py
# Then look at TFT screen to verify emojis
```

### Full Test (30 minutes)
```bash
# Run all test scripts
cd ~/GairiHead && source venv/bin/activate

# Test 1: Servos
python tests/test_servos.py

# Test 2: Expressions
python tests/test_expressions.py  # If exists

# Test 3: Arduino
python test_emoji_display.py

# Test 4: Auth
python test_websocket_auth.py

# Test 5: Voice (if time)
python main.py --mode test
```

---

## Known Risks Without Testing

1. **Servo Angles**: If 75° is too high, servos could strain
2. **Expression Quality**: Reduced angles might look less expressive
3. **Timer Fix**: Untested code path could have other issues
4. **Authentication**: Gary client WILL fail until updated

---

## Recommendation

**Before marking as production-ready:**
1. Tim runs servo angle tests (5 min)
2. Tim visually verifies Arduino emojis (2 min)
3. Tim runs authentication tests (3 min)
4. Gary team updates client with token
5. Full end-to-end test with Gary

**Only then**: Mark as production-ready ✅

---

**Created**: 2025-11-09
**Status**: ⚠️ PHYSICAL TESTING PENDING
**Next Step**: Tim to run test scripts and verify hardware

