# Bugs to Fix - From Comprehensive Review (2025-11-09)

**Source**: Comprehensive GairiHead review covering architecture, code, and configuration
**Session**: Documentation cleanup completed, bugs documented for next coding session

---

## Priority 0 - Security Issues (Remote Server)

### 1. Add WebSocket Authentication
**File**: `src/gairi_head_server.py`
**Issue**: Server accepts commands from anyone without authentication
**Risk**: High - anyone on network can control hardware
**Fix**: Implement token-based authentication
**Recommendation**:
- Add API key or JWT token validation
- Check token on each WebSocket connection
- Document in GARY_API_REFERENCE.md

### 2. Add Input Validation
**File**: `src/gairi_head_server.py`
**Issue**: No input validation on command parameters
**Risk**: Medium - command injection possible
**Fix**: Validate all parameters before execution
**Recommendation**:
- Whitelist allowed actions
- Validate parameter types and ranges
- Sanitize string inputs

### 3. Add Rate Limiting
**File**: `src/gairi_head_server.py`
**Issue**: No rate limiting per client
**Risk**: Medium - DoS vulnerability
**Fix**: Implement per-client request throttling
**Recommendation**:
- Max requests per minute per client IP
- Queue or reject excess requests
- Log suspicious activity

### 4. Network Binding Security
**File**: `src/gairi_head_server.py`
**Issue**: Binds to 0.0.0.0 (all interfaces), exposed to network
**Risk**: Medium - unnecessarily broad exposure
**Fix**: Bind to specific interface or add firewall rules
**Recommendation**:
- Bind to 127.0.0.1 for localhost only (if Gary is local)
- OR bind to Tailscale interface only
- OR document required firewall rules

---

## Priority 1 - Bugs (Hardware/Code)

### 5. Servo Timer Attribute Name Mismatch
**File**: `src/servo_controller.py:145`
**Issue**: References `detach_timer` but attribute is `_detach_timer` (with underscore)
**Impact**: Potential crash when detaching servo
**Fix**: Change `detach_timer` to `_detach_timer` throughout
**Line**: Approximately line 145

### 6. Expression Eye Angle Exceeds Physical Limit
**File**: `config/expressions.yaml`
**Issue**: Some expressions configure 80° eye angles, but physical limit is 75°
**Impact**: Servo strain, potential physical damage
**Fix**: Find all expressions with 80° and reduce to 75° or less
**Lines**: Multiple expressions need review
**Physical Limit**: Both eyelids calibrated to 0-75° range

### 7. Missing Arduino Emoji Mappings
**File**: `arduino/gairihead_display/gairihead_display.ino`
**Issue**: Some expressions don't have corresponding emoji mappings
**Impact**: Display shows blank or wrong emoji for some expressions
**Fix**: Add missing emoji mappings for all 24 expressions
**Current**: 10 emoji mappings exist
**Target**: 24 emoji mappings (one per expression)

### 8. Config References Unused Local Ollama
**File**: `config/gairi_head.yaml` (partially fixed)
**Issue**: Config implies local LLM processing, but all processing is remote
**Impact**: Confusion about architecture
**Fix**: Already updated with clarifying comments, but verify enabled flag is false
**Status**: PARTIALLY FIXED - comments added, verify `local_llm.enabled: false`

---

## Priority 2 - Improvements (Testing/Config)

### 9. Add Unit Tests for Core Modules
**Files**: Missing test files for:
- `tests/test_voice_handler.py`
- `tests/test_llm_tier_manager.py`
- `tests/test_expression_engine.py`
**Issue**: Only 56% test pass rate (9/16 passing)
**Impact**: Hard to verify changes don't break functionality
**Fix**: Add comprehensive unit tests
**Recommendation**:
- Test voice recording and TTS
- Test LLM tier routing logic
- Test expression transitions
- Mock GPIO/hardware where needed

### 10. Add webrtcvad to requirements.txt
**File**: `requirements.txt`
**Issue**: webrtcvad is installed and used but not in requirements.txt
**Impact**: Fresh install would be missing dependency
**Fix**: Add `webrtcvad` to requirements.txt
**Note**: Already installed on Pi, but needed for fresh deployments

### 11. Document/Remove Unused Ollama Installation
**Files**: System has Ollama installed with qwen2.5 models
**Issue**: Ollama is installed but completely unused
**Impact**: Consumes disk space, potential confusion
**Fix Options**:
1. Document as "future offline capability" (DONE in docs)
2. Uninstall Ollama and models to free space
3. Keep for local experimentation
**Recommendation**: Keep installed but documented as unused (already done)

### 12. Implement Graceful Shutdown in Server
**File**: `src/gairi_head_server.py`
**Issue**: Server may not clean up resources on exit
**Impact**: GPIO/hardware resources may stay locked
**Fix**: Add signal handlers for SIGTERM/SIGINT
**Recommendation**:
- Close camera properly
- Detach servos
- Close Arduino serial connection
- Close WebSocket connections

---

## Hardware Notes (From User Message)

**Microphone**: USB EMEET OfficeCore M0 Plus (not C920)
**Speaker**: USB EMEET OfficeCore M0 Plus (not C920)
**Camera**: Pi Camera Module 3 (arriving soon), currently using USB webcam

---

## Status Tracking

### Documentation (Completed This Session)
- ✅ README.md - Updated architecture section
- ✅ ARCHITECTURE.md - Clarified intelligence flow
- ✅ config/gairi_head.yaml - Added architecture comments
- ✅ GARY_API_REFERENCE.md - Added bidirectional note
- ✅ STATUS.md - Updated intelligence sections
- ✅ llm_tier_manager.py - Updated header comments
- ✅ voice_handler.py - Updated header comments
- ✅ main.py - Updated header comments + hardware list

### Bugs (To Fix Next Session)
- ⏸️ Priority 0: Security issues (#1-4)
- ⏸️ Priority 1: Hardware/code bugs (#5-8)
- ⏸️ Priority 2: Improvements (#9-12)

---

## Next Session Plan

1. **Security Hardening** (1-2 hours)
   - Add authentication to WebSocket server
   - Add input validation
   - Add rate limiting
   - Update bind address or firewall

2. **Bug Fixes** (30 minutes)
   - Fix servo timer attribute name
   - Fix expression eye angles
   - Add missing Arduino emoji mappings
   - Verify local_llm.enabled is false

3. **Testing Improvements** (optional, 1-2 hours)
   - Add webrtcvad to requirements.txt
   - Create unit test stubs for core modules
   - Implement graceful shutdown

---

**Created**: 2025-11-09
**Last Updated**: 2025-11-09
**Next Review**: After bug fixes implemented
