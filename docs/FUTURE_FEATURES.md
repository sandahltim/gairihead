# Future Features for GairiHead

## Voice-Activated Face Enrollment

**Priority**: Medium
**Estimated Effort**: 2-3 hours

### Feature Description
Allow users to register new authorized people via voice command instead of manual photo management.

### User Experience
```
User: "Gary, remember Jessica"
Gary: "Sure. Jessica, look at the camera."
      [Captures 15 photos over 30 seconds from different angles]
      [Saves to data/known_faces/jessica/]
      [Reloads face encodings]
Gary: "Got it. I'll remember Jessica."

User: "Gary, who is this?"
      [Shows camera to person]
Gary: "That's Jessica" (if recognized)
      "I don't recognize them" (if unknown)
```

### Implementation Steps

1. **Add voice intents to LLM tier manager**
   - Detect phrases: "remember [name]", "add [name]", "register [name]"
   - Extract name from query
   - Return intent: `enroll_face` with parameter `name`

2. **Create enrollment mode in main.py**
   ```python
   async def enroll_new_person(self, name: str):
       # 1. Announce enrollment starting
       # 2. Capture 15-20 photos over 30 seconds
       # 3. Validate faces detected in photos
       # 4. Save to data/known_faces/{name}/
       # 5. Reload VisionHandler.known_faces
       # 6. Confirm completion
   ```

3. **Photo capture loop**
   - Capture every 2 seconds for 30 seconds (15 photos)
   - Show different prompts: "Turn left", "Turn right", "Smile", "Serious"
   - Validate face detected in each frame before saving
   - Display via Arduino: "Photo 5/15..."

4. **Integration points**
   - Wire intent detection in `llm_tier_manager.py`
   - Add handler in `main.py`
   - Update Arduino display for enrollment UI
   - Add confirmation expression (maybe "pride" after successful enrollment)

5. **Authorization levels**
   - Default to level 2 (guest) for voice-enrolled users
   - Only Tim (level 1) can enroll new people
   - Add voice command: "Gary, make Jessica level 1" (upgrade authorization)

### Current Manual Method

Until implemented, add people manually:

```bash
# 1. Create directory
mkdir -p /home/tim/GairiHead/data/known_faces/jessica

# 2. Add 10-20 photos (various angles, lighting)
# Photos named: jessica_001.jpg, jessica_002.jpg, etc.

# 3. System auto-loads on next face recognition
# Or restart GairiHead to force reload
```

### Related Files
- `src/llm_tier_manager.py` - Intent detection
- `src/vision_handler.py` - Face enrollment logic
- `main.py` - Enrollment mode handler
- `src/arduino_display.py` - UI feedback during enrollment

### Security Considerations
- Only allow enrollment when Tim (level 1) is present
- Require voice confirmation: "Gary, confirm enrollment"
- Add ability to remove people: "Gary, forget [name]"
- Log all enrollment events

---

## Other Future Features

### Gesture Recognition
Recognize hand gestures for silent commands (wave = hello, thumbs up = acknowledge, etc.)

### Emotion Detection
Detect user emotions (frustrated, happy, confused) and adjust Gary's tone accordingly.

### Multi-Person Tracking
Track multiple people in frame, direct attention to speaker.

### Voice Enrollment
Voice print recognition in addition to face recognition.

### Proactive Greeting Improvements
- Time-of-day awareness (morning grumpy mode)
- Remember previous conversation context
- Detect when Tim is stuck on a problem
