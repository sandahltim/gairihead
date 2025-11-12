# Voice-Authorized Face Enrollment

**Security Feature**: Only Tim (Level 1) can enroll new faces using voice commands.

---

## Overview

GairiHead now supports voice-authorized face enrollment with **Tim's voice verification**:
- ✅ Face recognition confirms identity (Level 1 = Tim)
- ✅ Voice command triggers enrollment
- ✅ Fully guided voice and visual prompts
- ✅ New users registered as Guest (Level 2)

---

## How It Works

### Security Flow:
```
1. Tim taps CENTER button
   ↓
2. Face scan → Recognizes Tim (Level 1) ✅
   ↓
3. Tim says: "Gary, register new face"
   ↓
4. System verifies: Is speaker Level 1? ✅
   ↓
5. Enrollment flow begins
```

**If Level 2 or 3 tries:** Command ignored (not even processed)

---

## Usage

### Step-by-Step:

**1. Tim initiates interaction:**
```
[Tap CENTER button on Arduino display]
```

**2. Face scan confirms identity:**
```
Display: "Authorized: Tim (Level 1, confidence 0.95)"
```

**3. Tim says enrollment command:**
```
"Gary, register new face"
# OR any of these:
"Gary, add new face"
"Gary, enroll new face"
"Gary, add new user"
"Gary, register new person"
```

**4. Gary asks for name:**
```
Gary: "What is the person's name?"
[Wait for prompt]
Tim: "Sarah"
```

**5. Photo collection begins:**
```
Gary: "Okay, registering Sarah. Please have them look at the camera."
[1 second pause]
Gary: "Starting photo collection. Please look at the camera and move
       your head through different angles."
```

**6. Automated photo capture:**
```
- 20 photos collected over ~40 seconds
- Every 2 seconds: auto-capture
- Prompts on display for different angles
- GairiHead shows "alert" expression (watching)
```

**7. Completion:**
```
Gary: "Success! Sarah has been registered as a guest.
       They now have Level 2 access."
Display: "✅ Sarah registered as guest (Level 2)"
GairiHead: Happy expression
```

---

## Voice Commands

### Enrollment Phrases (Any triggers it):
- "register new face"
- "add new face"
- "enroll new face"
- "add a new face"
- "register a face"
- "add new user"
- "register new person"
- "add new person"

**Case insensitive** - all variations work!

---

## Authorization Levels

### Tim (Level 1):
- ✅ Can enroll new faces
- ✅ Full Gary access (all tools)
- ✅ Training data logged

### New Guest (Level 2):
- ✅ Basic Gary access
- ⚠️ Limited tools (no sensitive ops)
- ❌ Cannot enroll others
- ❌ Training not logged

### Stranger (Level 3):
- ❌ No enrollment access
- ❌ Local-tier only (no cloud)
- ❌ No training logged

---

## Photo Collection Details

### Automatic Capture:
- **Count**: 20 photos
- **Interval**: 2 seconds between shots
- **Duration**: ~40 seconds total
- **Guidance**: On-screen prompts for angles
- **Timeout**: 2 minutes max (safety)

### Angles Captured:
1. Forward (straight)
2. Left profile
3. Right profile
4. Looking up
5. Looking down
6. Various expressions

### Storage:
```
/home/tim/GairiHead/data/known_faces/{name}/
├── {name}_*.jpg       # 20 training photos
└── metadata.json      # Enrollment details
```

---

## Metadata Stored

Each enrolled user gets metadata:
```json
{
  "username": "sarah",
  "authorization_level": 2,
  "photos_collected": 20,
  "collection_date": "2025-11-12T...",
  "description": "Guest user",
  "enrolled_by": "tim",
  "enrollment_method": "voice_authorized"
}
```

---

## Security Features

### 1. Face Verification First
- Face scan happens BEFORE voice command
- Must be recognized as Tim (Level 1)
- Level 2/3 cannot trigger enrollment

### 2. Voice Command Check
- Transcription checked locally (not sent to Gary)
- Special command bypasses normal query
- Prevents accidental Gary responses

### 3. Audio Not Logged
- Enrollment audio not sent to Gary
- Name transcription local-only
- Privacy preserved

### 4. Guest-Only Registration
- New users always Level 2 (Guest)
- Cannot be escalated without manual edit
- Limits potential security risk

---

## Error Handling

### If Name Not Heard:
```
Gary: "Sorry, I didn't hear a name. Enrollment cancelled."
```

### If Photo Collection Fails:
```
Gary: "Sorry, photo collection failed. Please try again."
Expression: Confused
```

### If Timeout (>2 minutes):
```
Gary: "Enrollment took too long. Please try again."
```

### If Camera Unavailable:
```
Gary: "Camera not available. Please check hardware."
```

---

## Display States During Enrollment

### 1. Scanning (Face Recognition):
```
State: "scanning"
Expression: "alert"
User: "unknown" → "tim" (when recognized)
```

### 2. Enrolling (Photo Collection):
```
State: "enrolling"
Expression: "alert"
User: "{new_name}"
Level: 2
```

### 3. Success:
```
View: Conversation
User: "Register {name}"
Gairi: "✅ {name} registered as guest (Level 2)"
Expression: "happy"
```

---

## Testing

### Test Enrollment Flow:
```bash
# 1. Start GairiHead in production mode
python main.py --mode production

# 2. Tap CENTER button
# 3. Wait for face scan (should recognize Tim)
# 4. Say: "Gary, register new face"
# 5. When asked, say a name: "TestUser"
# 6. Watch display for photo collection
# 7. Wait for completion confirmation

# 8. Verify files created:
ls -lh ~/GairiHead/data/known_faces/testuser/
# Should see: 20 .jpg files + metadata.json
```

### Verify Level 2 Assignment:
```bash
cat ~/GairiHead/data/known_faces/testuser/metadata.json
# Check: "authorization_level": 2
```

### Test Recognition:
```bash
# Next button press should recognize new user
# Display should show: "Authorized: TestUser (Level 2)"
```

---

## Removing Users

### Manual Removal:
```bash
# Remove user's face data
rm -rf ~/GairiHead/data/known_faces/{username}/

# GairiHead will reload known faces on next restart
```

### Via Script (Future):
```bash
# Not yet implemented - coming soon
python scripts/remove_face.py username
```

---

## Troubleshooting

### "Command Not Detected"
- **Check**: Was Tim recognized as Level 1?
- **Fix**: Make sure face scan completes before speaking
- **Tip**: Wait for display to show "Authorized: Tim"

### "Photo Collection Failed"
- **Check**: Is camera connected? `ls /dev/video*`
- **Fix**: Restart GairiHead: `sudo systemctl restart gairihead`
- **Tip**: Test camera: `python scripts/test_camera.py`

### "Name Not Transcribed Correctly"
- **Tip**: Speak clearly and slowly
- **Tip**: Use simple names (1-2 syllables)
- **Note**: Name auto-cleaned (lowercase, no spaces)

### "Enrollment Timed Out"
- **Cause**: Photo collection took >2 minutes
- **Fix**: Ensure person stays in frame
- **Fix**: Check camera not blocked/covered

---

## Future Enhancements

### Planned Features:
- [ ] Voice command to **remove** faces
- [ ] Voice command to **list** registered users
- [ ] Web interface for face management
- [ ] Video preview during enrollment
- [ ] Retry failed photo captures
- [ ] Bulk enrollment mode

---

## Architecture Notes

### Code Location:
- **Command Handler**: `main.py:483-511` (`_check_special_command`)
- **Enrollment Flow**: `main.py:513-601` (`enroll_new_face`)
- **Voice Integration**: `main.py:376-440` (handle_interaction)

### Dependencies:
- `scripts/collect_face_photos_headless.py` - Photo collection
- `src/vision_handler.py` - Face recognition
- `src/voice_handler.py` - STT/TTS

### Security Model:
```python
# Authorization check (main.py:399-402)
if authorization['level'] == 1:  # Tim only
    if await self._check_special_command(transcription):
        return  # Command handled, skip Gary
```

---

## Examples

### Example Session Log:
```
[INFO] Interaction #5
[INFO] 👁️  Step 1: Scanning for face authorization...
[INFO] 🔐 Authorization: Level 1 (Main User)
[INFO]    User: tim, Confidence: 0.95
[INFO] 🎤 Step 2: Ready for voice query...
[INFO] 🎤 Recording audio...
[INFO] 📝 Transcribed: "register new face"
[INFO] 🎯 Face enrollment command detected (Tim authorized)
[INFO] ============================================================
[INFO] FACE ENROLLMENT MODE
[INFO] ============================================================
[INFO] 🎤 Listening for name...
[INFO] 📝 Name captured: sarah
[INFO] 📸 Starting photo collection for sarah...
[SUCCESS] ✅ Face photos collected for sarah
[SUCCESS] ✅ sarah enrolled successfully as Level 2 (Guest)
[SUCCESS] ✅ Interaction #5 complete
```

---

**Voice-Authorized Face Enrollment** is now live! 🎉

Only Tim can add new faces by speaking the command after face verification.
