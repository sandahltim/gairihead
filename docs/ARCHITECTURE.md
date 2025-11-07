# GairiHead Architecture

**Two-tier intelligence system: Local monitoring + Cloud reasoning**

---

## Design Philosophy

**Problem**: Running every "Hey Gary, what time is it?" through Haiku = $$$
**Solution**: Local LLM for ambient monitoring, escalate to Haiku for business logic

**Analogy**: Your brain doesn't fire up the prefrontal cortex to scratch your nose. Same principle.

---

## Intelligence Tiers

### Tier 1: Local LLM (Llama 3.2 3B)

**What it handles**:
- Wake word processing ("Yeah?" "What's up?")
- Ambient monitoring ("Tim looks frustrated")
- Simple queries ("What time is it?")
- Context gathering for escalation
- Motion/face detection processing
- Vision analysis ("Tim's at his desk")

**Why local**:
- Cost: $0 (runs on Pi 5 GPU)
- Latency: ~300-500ms
- Privacy: No camera feed to cloud
- Always-on: No API rate limits

**Example interactions**:
```
Tim: "Hey Gary"
Local: "Yeah?" [eyes flash blue]

Tim: "What time is it?"
Local: "3:47pm" [simple, no escalation]

Tim: [stares at screen for 10 minutes]
Local: [Detects frustration] "You okay?" [proactive, no escalation]
```

### Tier 2: Claude Haiku 3.5 (Cloud)

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
Local: [Detects business query] → Escalate to Haiku
Haiku: "Hmmmm... Friday's at 12 deliveries, 3 stores..."
[Uses operations_schedule_tool, full personality]

Tim: "Should I pull from Elk River?"
Local: [Detects complex reasoning] → Escalate to Haiku
Haiku: "Well... Elk River's at 33 tables available, 20min drive..."
[Multi-step reasoning, recommendations]
```

---

## Escalation Decision Logic

```python
def should_escalate_to_haiku(query: str, context: dict) -> bool:
    """
    Decide whether to use local LLM or escalate to Haiku

    Local handles:
    - Time queries
    - Simple greetings
    - Ambient observations
    - Wake word responses

    Haiku handles:
    - Business queries (contracts, schedule, inventory)
    - Multi-step reasoning
    - Tool calling requirements
    - Personality-critical responses
    """

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

    # Simple queries stay local
    if query.lower().startswith(('what time', 'hey', 'hello')):
        return False

    # Default: escalate (safe choice)
    return True
```

---

## Data Flow

### Wake Word → Response

```
1. USB Mic captures audio
   ↓
2. Local wake word detection (Porcupine)
   ↓
3. Eyes flash blue (listening state)
   ↓
4. Capture full query via STT
   ↓
5. Local LLM analyzes query
   ↓
   ├─ Simple? → Local LLM responds
   │            ↓
   │            Eyes show "talking" state
   │            ↓
   │            TTS output + mouth animation
   │
   └─ Complex? → Escalate to Haiku
                  ↓
                  Eyes show "thinking" state
                  ↓
                  Websocket to main Gary service
                  ↓
                  Gary executes tools, returns response
                  ↓
                  TTS output + mouth animation
```

### Proactive Monitoring

```
1. Camera continuously monitors (5 FPS)
   ↓
2. Local LLM analyzes frames
   - Face detection (OpenCV)
   - Motion tracking
   - Posture/attention analysis
   ↓
3. Detects interesting events:
   - Tim walks in
   - Tim looks frustrated
   - Stranger appears
   - Calendar alert time (2pm Thursday)
   ↓
4. Local LLM decides:
   - Ignore (not interesting)
   - Comment locally ("Morning!")
   - Escalate to Haiku ("Friday's schedule is chaos...")
   ↓
5. Trigger proactive speech
   Eyes → Alert state
   TTS → Proactive message
   Mouth → Animated
```

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

### Pi 5 ↔ Main Gary Service (Websocket)

**Purpose**: Escalate queries to full Gary intelligence

**Protocol**: JSON over websocket
```json
// GairiHead → Gary Service (query)
{
  "type": "voice_query",
  "text": "What's Friday's schedule?",
  "user": "tim",
  "context": {
    "vision": "Tim at desk, looking at monitor",
    "time": "2025-11-06 16:30",
    "location": "office",
    "recent_activity": "Reviewing calendar"
  }
}

// Gary Service → GairiHead (response)
{
  "type": "response",
  "text": "Hmmmm... Friday's at 12 deliveries...",
  "expression": "thinking",
  "tool_calls": ["operations_schedule"],
  "tokens": {
    "input": 1250,
    "output": 890,
    "cost": 0.004
  }
}
```

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

## Local LLM Integration

**Model**: Llama 3.2 3B Instruct (quantized to 4-bit)
**Runtime**: Ollama on Pi 5
**Memory**: ~2GB VRAM
**Speed**: ~30 tokens/sec on Pi 5

**System Prompt** (stripped down for speed):
```
You are Gary, a former deep-space robot now assisting with office tasks.

You handle simple queries and ambient monitoring.
For complex business questions, say "LET_ME_THINK" to escalate.

Be brief, witty, helpful. You're monitoring Tim's office.

Examples:
- "What time is it?" → "3:47pm"
- "Hey Gary" → "Yeah?"
- "What's Friday's schedule?" → "LET_ME_THINK" (escalate)
```

**Escalation trigger**: Local LLM outputs `LET_ME_THINK` → Pi 5 escalates to Haiku

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
