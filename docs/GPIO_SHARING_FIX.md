# GPIO Sharing Fix - Gary Remote Control

## Problem
Gary's remote control API was getting "GPIO busy" errors when trying to control servos because the main app held GPIO pins permanently.

## Root Cause
1. **Main app startup**: Initialized ServoController at startup, claiming GPIO pins 17, 22, 27
2. **Server access blocked**: When server tried to create its own ServoController, GPIO pins were already in use
3. **Process isolation**: Linux GPIO can only be accessed by one process at a time

## Solution: Lazy Servo Initialization

### Changes Made

#### 1. ServoController.close() method (src/servo_controller.py)
```python
def close(self):
    """Fully close servos and release GPIO pins (allows other processes to access)"""
    # Cancel pending detach timers
    if hasattr(self, 'detach_timer') and self.detach_timer:
        self.detach_timer.cancel()

    # Close all servos (releases GPIO pins)
    self.left_eyelid.close()
    self.right_eyelid.close()
    self.mouth.close()
```

#### 2. Main App Lazy Initialization (main.py)
**Startup (initialize()):**
- Expression engine initialized
- Servo controller set to None (NOT initialized)
- Log: "Expression engine initialized (servos lazy-loaded)"

**Interaction Start (handle_interaction()):**
```python
# Initialize servos if not already done (lazy init)
if self.servo_controller is None and self.expression_engine:
    self.servo_controller = ServoController(config_path=str(self.config_path))
    self.expression_engine.set_controllers(
        servo_controller=self.servo_controller,
        arduino_display=self.arduino_display
    )
```

**Interaction End (handle_interaction() finally block):**
```python
# Close servos to release GPIO pins for server access
if self.servo_controller:
    self.servo_controller.close()
    self.servo_controller = None
```

### Benefits

1. **GPIO Available for Server**: Main app only claims GPIO during active interactions (~30-60 seconds)
2. **No GPIO Conflicts**: Server can access GPIO between local interactions
3. **Automatic Coordination**: Works seamlessly with hardware_coordinator.py priority system
4. **Power Efficiency**: Servos only powered when actually in use

## Testing Results

### Test 1: Speak Command
```bash
gary → gairihead.speak("Success! Gary can now control GairiHead")
```
**Result:** ✅ SUCCESS
- Hardware lock acquired (remote)
- Servos initialized successfully
- Expression set to "happy"
- TTS spoke text (5.5 seconds)
- Arduino display updated
- Hardware lock released

### Test 2: Expression Command
```bash
gary → gairihead.set_expression("sarcasm")
```
**Result:** ✅ SUCCESS
- Hardware lock acquired (remote)
- Expression changed successfully
- Hardware lock released

### Test 3: Lock Release Verification
**Result:** ✅ VERIFIED
- Lock properly released after each command
- No stale locks blocking subsequent commands
- Multiple commands can be sent in sequence

## Architecture

```
Main App (PID 73803)                  Server (PID 69978)
==================                    ==================

Startup:
- servos = None                       - servos = None
  (GPIO pins free)                      (GPIO pins free)

Button Press:
1. Acquire lock ────────────────────> Lock unavailable
2. Init servos (claim GPIO)           (waiting...)
3. Run interaction
4. Close servos (release GPIO)
5. Release lock ────────────────────> Lock available!
  (GPIO pins free)

                                      Remote Command:
  Lock unavailable <────────────────  1. Acquire lock
  (waiting...)                        2. Init servos (claim GPIO)
                                      3. Execute command
                                      4. Close servos (release GPIO)
                                      5. Release lock
                                        (GPIO pins free)
```

## Files Modified

1. **src/servo_controller.py**: Added close() method
2. **main.py**: Lazy servo initialization, close on interaction end
3. **src/hardware_coordinator.py**: (Previously implemented) Priority-based locking

## Commits

1. `972c560`: fix: Ensure hardware lock always released in main app
2. `d189c50`: feat: Lazy servo initialization for GPIO sharing between processes

## Current Status

✅ **FULLY OPERATIONAL**

Gary can now:
- Send speak commands with TTS + mouth animation + expressions
- Change facial expressions remotely
- All commands work while main app runs normally
- Hardware coordination automatic (no manual mode switching)
- Local user sees Arduino display during remote control

**Date:** 2025-11-08
**Session:** GPIO sharing implementation and testing
