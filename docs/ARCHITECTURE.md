# GairiHead Architecture

**Thin client hardware interface for Gary's centralized intelligence system**

---

## Design Philosophy

**Architecture**: GairiHead = Hardware Interface Layer → Gary Server = All Intelligence Processing

**Problem**: Running every "Hey Gary, what time is it?" through Haiku = $$$
**Solution**: Gary's two-tier LLM system (Qwen local + Haiku cloud), GairiHead just routes queries

**Key Insight**: GairiHead does NO local LLM processing. It's a beautifully engineered hardware controller (voice I/O, camera, servos, display) that delegates ALL AI intelligence to Gary server.

**Analogy**: GairiHead is the body, Gary server is the brain.

---

## Intelligence Tiers (Gary Server)

**IMPORTANT**: Both tiers run on Gary server, NOT on the Pi. GairiHead only sends audio/queries via WebSocket.

### Tier 1: Qwen 2.5 Coder 7B (Gary's Local LLM)

**What it handles** (decided by Gary, not GairiHead):
- Wake word processing ("Yeah?" "What's up?")
- Ambient monitoring ("Tim looks frustrated")
- Simple queries ("What time is it?")
- Context gathering for escalation
- Stranger interactions (security: no cloud access for unknowns)
- Vision analysis ("Tim's at his desk")

**Why local (on Gary)**:
- Cost: $0 (runs on Gary's GPU)
- Latency: ~300-500ms (over LAN to Gary)
- Privacy: No camera feed to external cloud
- Always-on: No API rate limits

**Example interactions**:
```
Tim: "Hey Gary"
GairiHead → Gary (Qwen): "Yeah?" [GairiHead eyes flash blue]

Tim: "What time is it?"
GairiHead → Gary (Qwen): "3:47pm" [simple, no escalation]

Tim: [stares at screen for 10 minutes]
GairiHead camera → Gary (Qwen): [Detects frustration] "You okay?" [proactive, no escalation]
```

### Tier 2: Claude Haiku 4.5 (Cloud via Gary)

**What it handles**:
- Business intelligence queries
- Contract/schedule lookups
- Multi-step reasoning
- Tool calling (accessing Gary's tools)
- Complex personality responses
- Strategic recommendations

**Why cloud**:
- Quality: Better reasoning than local models
- Tools: Access to all Gary's business tools
- Personality: Full Gary character depth
- Memory: Vector search, long-term context

**Cost optimization**:
- Only escalates when necessary
- Token-efficient-tools enabled
- Caches common queries locally

**Example interactions**:
```
Tim: "What's Friday's schedule?"
GairiHead → Gary (Qwen): [Detects business query] → Escalate to Haiku
GairiHead ← Gary (Haiku): "Hmmmm... Friday's at 12 deliveries, 3 stores..."
[Gary uses operations_schedule_tool, full personality, routes back to GairiHead]

Tim: "Should I pull from Elk River?"
GairiHead → Gary (Qwen): [Detects complex reasoning] → Escalate to Haiku
GairiHead ← Gary (Haiku): "Well... Elk River's at 33 tables available, 20min drive..."
[Multi-step reasoning on Gary, recommendations routed to GairiHead]
```

---

## Escalation Decision Logic (Gary Server)

**IMPORTANT**: This logic runs on Gary server, NOT on GairiHead. GairiHead just sends the query and receives the response.

```python
def should_escalate_to_haiku(query: str, context: dict) -> bool:
    """
    [Runs on Gary Server]
    Decide whether to use Qwen (local) or escalate to Haiku (cloud)

    Qwen handles:
    - Time queries
    - Simple greetings
    - Ambient observations
    - Wake word responses
    - Stranger interactions (security)

    Haiku handles:
    - Business queries (contracts, schedule, inventory)
    - Multi-step reasoning
    - Tool calling requirements
    - Personality-critical responses
    - Main user (Level 1) complex queries
    """

    # Security: Strangers NEVER get cloud access (handled on Gary)
    if context.get('authorization', {}).get('level') == 3:
        return False  # Force Qwen for strangers

    # Keywords that trigger escalation
    business_keywords = [
        'contract', 'delivery', 'schedule', 'customer',
        'inventory', 'friday', 'equipment', 'order'
    ]

    # Tool names (always escalate if tools needed)
    if any(tool in query.lower() for tool in [
        'schedule', 'contract', 'weather', 'customer'
    ]):
        return True

    # Business context
    if any(kw in query.lower() for kw in business_keywords):
        return True

    # Complex questions (how, why, should)
    if query.lower().startswith(('how ', 'why ', 'should ')):
        return True

    # Simple queries stay local (Qwen)
    if query.lower().startswith(('what time', 'hey', 'hello')):
        return False

    # Default: escalate (safe choice)
    return True
```

---

## Data Flow

### Wake Word → Response (GairiHead Hardware Flow)

```
1. GairiHead USB Mic captures audio
   ↓
2. GairiHead detects silence (VAD) or button press
   ↓
3. GairiHead eyes flash blue (listening state)
   ↓
4. GairiHead sends audio to Gary via WebSocket
   ↓
5. Gary Server processes (STT → LLM tier selection)
   ↓
   ├─ Simple? → Gary (Qwen) responds
   │            ↓
   │            GairiHead receives response
   │            ↓
   │            GairiHead eyes show "talking" state
   │            ↓
   │            GairiHead TTS output + mouth animation
   │
   └─ Complex? → Gary escalates to Haiku
                  ↓
                  GairiHead eyes show "thinking" state (purple)
                  ↓
                  Gary executes tools, returns response
                  ↓
                  GairiHead receives response
                  ↓
                  GairiHead TTS output + mouth animation
```

**Key**: GairiHead only handles hardware (mic, eyes, servos, speaker). Gary handles ALL intelligence.

### Proactive Monitoring (Future Feature)

```
1. GairiHead camera continuously monitors (5 FPS)
   ↓
2. GairiHead face detection (OpenCV local)
   - Face detection (OpenCV on Pi)
   - Motion tracking (OpenCV on Pi)
   - Basic frame analysis
   ↓
3. GairiHead sends frames to Gary for analysis
   ↓
4. Gary analyzes with Qwen:
   - Tim walks in
   - Tim looks frustrated
   - Stranger appears
   - Calendar alert time (2pm Thursday)
   ↓
5. Gary decides response:
   - Ignore (not interesting)
   - Comment with Qwen ("Morning!")
   - Escalate to Haiku ("Friday's schedule is chaos...")
   ↓
6. GairiHead triggers proactive speech
   Eyes → Alert state (hardware)
   TTS → Proactive message (hardware)
   Mouth → Animated (hardware)
```

**Key**: Even "local" face detection triggers send frames to Gary for intelligence processing. GairiHead's OpenCV just does basic detection, not analysis.

---

## Communication Protocols

### Pi 5 ↔ Pi Pico (UART)

**Purpose**: Send eye expression commands to NeoPixel controller

**Protocol**: Simple text commands, 115200 baud
```python
# Commands from Pi 5 to Pico:
"EXPR:idle"           # Set expression to idle (blue pulse)
"EXPR:thinking"       # Set expression to thinking (cyan chase)
"EXPR:alert"          # Set expression to alert (red flash)
"COLOR:255,0,0"       # Set solid color (RGB)
"BRIGHTNESS:128"      # Set brightness (0-255)
"ANIM:blink"          # Trigger blink animation
```

**Response**: Pico sends ACK
```python
"OK"                  # Command received and executing
"ERR:invalid"         # Invalid command
```

### Pi 5 ↔ Gary Server (Websocket) - PRIMARY INTELLIGENCE PATH

**Purpose**: ALL queries go to Gary (transcription, tier selection, LLM processing)

**Endpoint**: `ws://100.106.44.11:8765/ws` (Tailscale)

**Protocol**: JSON over websocket
```json
// GairiHead → Gary Server (audio + authorization)
{
  "audio": "<base64_wav_data>",
  "source": "gairihead",
  "process_full_pipeline": true,  // STT + LLM in one call
  "tier_preference": "auto",      // Gary decides Qwen vs Haiku
  "authorization": {
    "level": 1,                   // Face recognition level
    "user": "tim",
    "confidence": 0.95
  }
}

// Gary Server → GairiHead (full response)
{
  "transcription": "What's Friday's schedule?",
  "response": "Hmmmm... Friday's at 12 deliveries...",
  "tier": "cloud",                // Which tier Gary used
  "model": "haiku-4.5",
  "expression": "thinking",
  "tool_calls": ["operations_schedule"],
  "tokens": 2140,
  "time_ms": 1850
}
```

**Key**: GairiHead sends raw audio, Gary does EVERYTHING (STT, tier selection, LLM, tools), GairiHead just speaks the response.

---

## Expression Engine

**Maps Gary's state → Physical expressions**

```python
class ExpressionEngine:
    """
    Coordinates eyes, eyelids, and mouth for unified expressions
    """

    expressions = {
        'idle': {
            'eyes': {'color': 'blue', 'animation': 'pulse', 'speed': 'slow'},
            'eyelids': {'blink_rate': 8000},  # ms between blinks
            'mouth': {'position': 0}  # neutral
        },

        'listening': {
            'eyes': {'color': 'cyan', 'animation': 'solid', 'brightness': 200},
            'eyelids': {'open': True},  # Eyes wide
            'mouth': {'position': 10}  # Slight open
        },

        'thinking': {
            'eyes': {'color': 'cyan', 'animation': 'chase', 'speed': 'medium'},
            'eyelids': {'half_close': True},  # Pondering look
            'mouth': {'position': -5}  # Slight smirk
        },

        'alert': {
            'eyes': {'color': 'red', 'animation': 'flash', 'speed': 'fast'},
            'eyelids': {'wide': True},  # Alert/surprised
            'mouth': {'position': 30}  # Mouth open
        },

        'sarcasm': {
            'eyes': {'color': 'amber', 'animation': 'side_eye'},  # Dim one ring
            'eyelids': {'asymmetric': True},  # One eye narrower
            'mouth': {'position': -10}  # Smirk
        },

        'speaking': {
            'eyes': {'maintain_current': True},  # Don't change eyes during speech
            'eyelids': {'blink_sync': True},  # Blink on emphasis words
            'mouth': {'amplitude_driven': True}  # Move based on audio amplitude
        }
    }
```

---

## LLM Integration (Gary Server)

**CURRENT SETUP** (Production):
- **Model**: Qwen 2.5 Coder 7B (local tier on Gary)
- **Runtime**: Gary server (Tailscale 100.106.44.11:8765)
- **Memory**: Runs on Gary's GPU (not Pi)
- **Speed**: ~300-500ms over LAN
- **GairiHead Role**: Sends audio/text → Receives response

**FUTURE CAPABILITY** (If needed for offline/backup):
- **Model**: Ollama config present for Llama 3.2 3B
- **Runtime**: Could run on Pi 5 if Gary unavailable
- **Status**: Currently unused, kept for potential future use
- **Use case**: Offline mode, hardware improvements, local experiments

**System Prompt** (runs on Gary, not GairiHead):
```
You are Gary, a former deep-space robot now assisting with office tasks.

You handle simple queries and ambient monitoring (Qwen tier).
For complex business questions, escalate to Haiku tier.

Be brief, witty, helpful. You're monitoring Tim's office via GairiHead.

Examples:
- "What time is it?" → "3:47pm" (Qwen)
- "Hey Gary" → "Yeah?" (Qwen)
- "What's Friday's schedule?" → [Escalate to Haiku]
```

**Escalation trigger**: Gary's Qwen detects complexity → Gary escalates to Haiku → Response to GairiHead

---

## Vision Processing Pipeline

**Camera**: Pi Camera Module 3 Wide (120° FOV)
**FPS**: 5 FPS (low for power/processing)
**Resolution**: 640x480 (sufficient for face detection)

**Pipeline**:
```
1. Capture frame (640x480 @ 5 FPS)
   ↓
2. Face detection (OpenCV Haar Cascade)
   - Detects faces: Yes/No
   - Face positions (bounding boxes)
   ↓
3. Face recognition (optional)
   - Tim vs Stranger
   - Embeddings stored locally
   ↓
4. Scene analysis (Local LLM via vision)
   - "Tim at desk"
   - "Tim looking frustrated"
   - "Empty office"
   ↓
5. Trigger actions:
   - Eyes track largest face
   - Proactive greetings
   - Context for queries
```

---

## Power Management

**Total power draw**:
- Pi 5: 15W (under load)
- Pico: 0.5W
- Servos: 2W (peak, intermittent)
- NeoPixels: 1.5W (full brightness)
- USB peripherals: 3W
- **Total**: ~22W peak, ~12W idle

**Power supply**: 5V/5A USB-C (25W) for Pi 5, separate 5V/2A for servos/NeoPixels

**Optimization**:
- Dim eyes during idle (50% brightness)
- Reduce camera FPS when no motion detected
- Sleep local LLM between queries (wake on demand)

---

## Development Workflow

### Best Practices

1. **Hardware first**: Get servos/eyes working before AI
2. **Test in isolation**: Test each component separately
3. **Mock early**: Mock main Gary service for standalone testing
4. **Version lock**: Pin all dependency versions
5. **Git ignore**: Don't commit models or API keys

### Testing Strategy

**Unit tests**:
- Servo calibration (correct angles)
- NeoPixel animations (visual verification)
- UART communication (Pi 5 ↔ Pico)

**Integration tests**:
- Wake word accuracy (false positive rate)
- Escalation logic (local vs Haiku decisions)
- Expression sync (speech → mouth movement)

**System tests**:
- End-to-end voice query
- Proactive monitoring triggers
- Multi-turn conversations

---

## Cost Tracking

**Monthly estimates** (50 queries/day):
```
Local LLM queries:    30/day × 30 days = 900 queries  → $0
Haiku escalations:    20/day × 30 days = 600 queries  → ~$5-8

Total: ~$5-8/month for full office assistant
```

**Token optimization**:
- Local filters 60% of queries
- Haiku only sees business/complex queries
- Token-efficient-tools saves 14-70% on Haiku calls

---

## Security & Privacy

**Camera feed**:
- Processed locally only
- Never sent to cloud unless explicitly requested
- Face embeddings stored locally (encrypted)

**Voice data**:
- Wake word processed on-device
- Full queries sent to main Gary (already trusted)
- No third-party STT services

**Network**:
- Websocket to main Gary on local network
- No external services except Haiku API (via main Gary)

---

**Status**: Architecture complete, ready for implementation
**Next**: Build core modules (expression_engine.py, voice_handler.py)
