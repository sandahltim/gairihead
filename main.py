#!/usr/bin/env python3
"""
GairiHead Voice Assistant - Main Application (Hardware Controller)

ARCHITECTURE (Clarified):
- GairiHead = Hardware Interface (THIS APP - camera, mic, speaker, servos, display)
- Gary Server = ALL Intelligence (STT, LLM tiers, training data)
- This app: Orchestrates hardware → Routes to Gary → Outputs responses

Version: 1.0 (2025-11-07)
Purpose: Hardware orchestration for voice assistant with face recognition

Hardware:
- Microphone: USB EMEET OfficeCore M0 Plus
- Speaker: USB EMEET OfficeCore M0 Plus
- Camera: Pi Camera Module 3 (when it arrives), USB webcam (current)
- Servos: 3x MG90S (GPIO 17, 27, 22)
- Display: Arduino Mega 2560 + TP28017 2.8" TFT

Flow:
1. Initialize hardware components (camera, voice, servos, display)
2. Wait for interaction trigger (button press or continuous mode)
3. Capture face → Determine authorization level (Level 1-3)
4. Record audio from mic
5. Send audio + authorization to Gary server via WebSocket
6. Gary processes (STT + LLM tier selection + response)
7. Receive response from Gary
8. Speak response via TTS + animate mouth servo
9. Update Arduino display with conversation
10. Training data logged by Gary server (Level 1 users only)

Core Principles Applied:
- #6: Trust but verify (test each component before integration)
- #8: Do it well (proper error handling, simple first)
- #10: Fix root problems, not symptoms
"""

import asyncio
import signal
import sys
import time
from pathlib import Path
from datetime import datetime
from loguru import logger
import yaml

# Import GairiHead components
from src.voice_handler import VoiceHandler
from src.llm_tier_manager import LLMTierManager
from src.camera_manager import CameraManager
from src.vision_handler import VisionHandler
from src.arduino_display import ArduinoDisplay
from src.expression_engine import ExpressionEngine
from src.servo_controller import ServoController
from src.stage_actions import StageActionHandler


class GairiHeadAssistant:
    """Main voice assistant application"""
    
    def __init__(self, config_path: Path):
        """
        Initialize GairiHead assistant

        Args:
            config_path: Path to gairi_head.yaml config file
        """
        # Store config path
        self.config_path = config_path

        # Load config
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        logger.info("=== GairiHead Voice Assistant v1.0 ===")

        # Initialize components
        self.camera = None
        self.vision = None
        self.llm_manager = None
        self.arduino_display = None
        self.expression_engine = None
        self.voice = None
        self.stage_actions = None  # Stage direction handler (*nods*, *sighs*, etc.)

        # State
        self.running = False
        self.interaction_count = 0
        self.in_interaction = False  # Prevent overlapping interactions
        self.last_interaction_time = 0  # Timestamp of last interaction
        self.interaction_cooldown = 2.0  # Seconds to wait between interactions
        self.last_conversation = None  # Store last conversation for display persistence
        
    async def initialize(self) -> bool:
        """
        Initialize all components
        
        Returns:
            True if all critical components initialized, False otherwise
        """
        logger.info("Initializing components...")
        
        # 1. Camera Manager
        try:
            logger.info("1. Initializing camera (lazy mode - opens on first use)...")
            # Lazy init - camera opens on first use, closes after to save power
            # This allows server to use camera when main app is idle
            self.camera = CameraManager(config_path=None, lazy_init=True)
            logger.success("✅ Camera initialized (lazy mode)")
        except Exception as e:
            logger.error(f"❌ Camera initialization failed: {e}")
            self.camera = None
        
        # 2. Vision Handler (face recognition)
        try:
            logger.info("2. Initializing face recognition...")
            self.vision = VisionHandler(self.config)
            logger.success("✅ Face recognition initialized")
        except Exception as e:
            logger.error(f"❌ Face recognition initialization failed: {e}")
            self.vision = None
        
        # 3. LLM Tier Manager (REQUIRED)
        try:
            logger.info("3. Initializing LLM tier manager...")
            self.llm_manager = LLMTierManager(self.config)
            logger.success("✅ LLM manager initialized")
        except Exception as e:
            logger.error(f"❌ LLM manager initialization FAILED: {e}")
            logger.error("Cannot continue without LLM manager")
            return False

        # 4. Arduino Display (OPTIONAL)
        try:
            logger.info("4. Initializing Arduino display...")
            display_config = self.config.get('hardware', {}).get('arduino_display', {})
            enabled = display_config.get('enabled', False)

            if enabled:
                self.arduino_display = ArduinoDisplay(
                    port=display_config.get('port', '/dev/ttyACM0'),
                    baudrate=display_config.get('baudrate', 115200),
                    enabled=True
                )
                if self.arduino_display.connected:
                    logger.success("✅ Arduino display connected")
                else:
                    logger.warning("⚠️ Arduino display configured but not connected")
                    self.arduino_display = None
            else:
                logger.info("   Arduino display disabled in config")
        except Exception as e:
            logger.error(f"❌ Arduino display initialization failed: {e}")
            self.arduino_display = None

        # 4.5. Expression Engine (OPTIONAL - Servos initialized lazily on first use)
        try:
            logger.info("4.5. Initializing expression engine...")
            # ExpressionEngine expects directory path, not file path
            config_dir = self.config_path.parent
            self.expression_engine = ExpressionEngine(config_path=str(config_dir))

            # Servos NOT initialized at startup - lazy init on first interaction
            # This allows server process to access GPIO when not in use
            self.servo_controller = None
            logger.success("✅ Expression engine initialized (servos lazy-loaded)")
        except Exception as e:
            logger.warning(f"⚠️ Expression engine initialization failed: {e}")
            logger.info("   Continuing without servo expressions (software will still work)")
            self.expression_engine = None
            self.servo_controller = None

        # 5. Voice Handler (REQUIRED)
        try:
            logger.info("5. Initializing voice handler...")
            self.voice = VoiceHandler(
                self.config,
                llm_tier_manager=self.llm_manager,
                arduino_display=self.arduino_display,
                expression_engine=self.expression_engine
            )

            # Initialize stage actions handler (processes Gary's action metadata)
            logger.info("Initializing stage actions handler...")
            self.stage_actions = StageActionHandler(
                servo_controller=self.servos,
                expression_engine=self.expression_engine
            )
            logger.info(f"✅ Stage actions ready ({len(self.stage_actions.sound_cache)} sounds loaded)")
            logger.success("✅ Voice handler initialized")
        except Exception as e:
            logger.error(f"❌ Voice handler initialization FAILED: {e}")
            logger.error("Cannot continue without voice handler")
            return False
        
        logger.info("=" * 60)
        logger.success("✅ GairiHead initialized successfully")
        logger.info("=" * 60)
        
        return True
    
    def get_authorization(self) -> dict:
        """
        Determine authorization level through face recognition

        Returns:
            Authorization dict with level, user, confidence
        """
        # If camera/vision not available, default to stranger mode
        if self.camera is None or self.vision is None:
            logger.warning("No face recognition - defaulting to stranger mode")
            return {
                'level': 3,
                'user': 'unknown',
                'confidence': 0.0
            }

        try:
            # Capture frame (camera opens on first read)
            success, frame = self.camera.read_frame()
            if not success or frame is None:
                logger.warning("Failed to capture frame - defaulting to stranger mode")
                return {
                    'level': 3,
                    'user': 'unknown',
                    'confidence': 0.0
                }

            # Detect faces first
            faces = self.vision.detect_faces(frame)

            if not faces:
                logger.info("👤 No face detected - stranger mode")
                return {
                    'level': 3,
                    'user': 'unknown',
                    'confidence': 0.0
                }

            # Use the first (largest) detected face
            face_rect = faces[0]

            # Recognize face
            result = self.vision.recognize_face(frame, face_rect)

            if result['recognized']:
                logger.info(f"🎯 Recognized: {result['name']} (confidence: {result['confidence']:.2f})")

                # Map name to authorization level
                # Level 1: Main users (Tim)
                # Level 2: Guests (registered but limited access)
                # Level 3: Strangers (unknown faces)

                if result['name'].lower() == 'tim':
                    level = 1
                elif result['name'].lower() in ['guest1', 'guest2']:  # Example guest names
                    level = 2
                else:
                    level = 3

                return {
                    'level': level,
                    'user': result['name'],
                    'confidence': result['confidence']
                }
            else:
                logger.info("👤 Unknown face detected - stranger mode")
                return {
                    'level': 3,
                    'user': 'unknown',
                    'confidence': 0.0
                }

        except Exception as e:
            logger.error(f"Face recognition error: {e}")
            return {
                'level': 3,
                'user': 'unknown',
                'confidence': 0.0
            }

        finally:
            # Close camera after face detection to save power and allow server access
            if self.camera:
                self.camera.close()
    
    async def handle_interaction(self):
        """Handle a single voice interaction with proper UX flow"""
        # Check if already in interaction (prevent overlapping)
        if self.in_interaction:
            logger.warning("⚠️ Already in interaction, ignoring trigger (button pressed while busy)")
            return

        # Check cooldown period
        time_since_last = time.time() - self.last_interaction_time
        if time_since_last < self.interaction_cooldown:
            logger.info(f"⏳ Cooldown active ({time_since_last:.1f}s < {self.interaction_cooldown}s), please wait")
            return

        # Check if Gary is using hardware remotely
        from src.hardware_coordinator import get_coordinator
        coordinator = get_coordinator()

        # Try to acquire lock (local = normal priority, short timeout)
        if not coordinator.acquire(timeout=0.5, is_remote=False):
            logger.info("⏸️  Gary is using GairiHead remotely - local interaction blocked")
            # Show message on display if available
            if self.arduino_display and self.arduino_display.connected:
                self.arduino_display.show_conversation(
                    user_text="",
                    gairi_text="Gary is using me remotely...",
                    expression="idle",
                    tier="gary",
                    response_time=0.0
                )
            return

        try:
            # Mark as in interaction
            self.in_interaction = True
            self.interaction_count += 1

            logger.info(f"\n{'=' * 60}")
            logger.info(f"Interaction #{self.interaction_count}")
            logger.info(f"{'=' * 60}")

            # Initialize servos if not already done (lazy init)
            if self.servo_controller is None and self.expression_engine:
                try:
                    logger.debug("Lazy-initializing servos for local interaction...")
                    from src.servo_controller import ServoController
                    self.servo_controller = ServoController(config_path=str(self.config_path))
                    self.expression_engine.set_controllers(
                        servo_controller=self.servo_controller,
                        arduino_display=self.arduino_display
                    )
                    logger.debug("Servos initialized successfully")
                except Exception as servo_error:
                    logger.warning(f"Servo init failed (continuing without servos): {servo_error}")
                    self.servo_controller = None

            # Step 1: Visual scan for authorization (HAPPENS ON BUTTON PRESS)
            logger.info("👁️  Step 1: Scanning for face authorization...")

            # Update Arduino display: Scanning state
            if self.arduino_display and self.arduino_display.connected:
                self.arduino_display.update_status(
                    state="scanning",
                    expression="alert",
                    user="unknown",
                    level=3,
                    confidence=0.0
                )

            # Update expression: alert (looking at user)
            if self.expression_engine:
                try:
                    self.expression_engine.set_expression('alert')
                except:
                    pass

            # Perform face recognition
            authorization = self.get_authorization()

            auth_level_name = {1: 'Main User', 2: 'Guest', 3: 'Stranger'}
            logger.info(f"🔐 Authorization: Level {authorization['level']} ({auth_level_name[authorization['level']]})")
            logger.info(f"   User: {authorization['user']}, Confidence: {authorization['confidence']:.2f}")

            # Update Arduino with authorization result
            if self.arduino_display and self.arduino_display.connected:
                self.arduino_display.update_status(
                    state="authorized",
                    expression="idle",
                    user=authorization['user'],
                    level=authorization['level'],
                    confidence=authorization['confidence']
                )

            # Brief pause to show authorization result
            await asyncio.sleep(0.5)

            # Step 2: Voice interaction
            logger.info("🎤 Step 2: Ready for voice query...")
            logger.info("   (Speak when ready - stops automatically when done)")

            try:
                # Record audio
                logger.info("🎤 Recording audio with VAD (speak when ready)...")
                logger.debug(f"VAD settings: max_duration={self.voice.vad_max_duration}s, silence={self.voice.vad_silence_duration}s, aggressiveness={self.voice.vad_aggressiveness}")

                audio = self.voice.record_audio_with_vad(
                    max_duration=self.voice.vad_max_duration,
                    silence_duration=self.voice.vad_silence_duration,
                    vad_aggressiveness=self.voice.vad_aggressiveness
                )

                if audio is None:
                    logger.warning("⚠️ No audio recorded - VAD timeout or no speech detected")
                    logger.info("   Possible causes: 1) No speech detected, 2) Microphone issue, 3) VAD sensitivity too high")
                    return

                logger.info(f"✅ Audio recorded successfully ({len(audio)} samples)")

                # Transcribe to check for special commands BEFORE sending to Gary
                transcription = self.voice.transcribe_audio(audio, authorization)

                if not transcription:
                    logger.warning("⚠️ Transcription failed")
                    return

                logger.info(f"📝 Transcribed: \"{transcription}\"")

                # Check for special commands (Tim-only) BEFORE processing with Gary
                if authorization['level'] == 1:  # Tim only
                    if await self._check_special_command(transcription):
                        # Special command handled, skip normal query
                        return

                # Not a special command - process normally with Gary
                # Update expression: thinking
                if self.expression_engine:
                    try:
                        self.expression_engine.set_expression('thinking')
                    except:
                        pass

                # Send to Gary for full processing
                result = self.voice.llm_manager.process_audio_query(audio, self.voice.sample_rate, authorization)

                if result and result.get('response'):
                    response_text = result['response']

                    # Get emotion for voice modulation from Gary's response
                    # Handle both single emotion (string) and multiple emotions (list)
                    emotion_data = result.get('emotion', 'idle')
                    if isinstance(emotion_data, list) and len(emotion_data) > 0:
                        current_emotion = emotion_data[0]  # Use primary (first) emotion
                        logger.info(f"🎭 Gary returned emotions: {emotion_data} (using primary: {current_emotion})")
                    else:
                        current_emotion = emotion_data if isinstance(emotion_data, str) else 'idle'
                        logger.info(f"🎭 Gary returned emotion: {current_emotion}")

                    # Set visual expression to match emotion (eyes + eyelids)
                    if result.get('emotion') and self.expression_engine:
                        try:
                            self.expression_engine.set_expression(result['emotion'])
                            logger.info(f"🎭 Expression & Voice: {current_emotion}")
                        except:
                            pass

                    # Process stage actions from Gary's metadata (winks, LED patterns, pauses, sounds)
                    if self.stage_actions and result.get('actions'):
                        try:
                            await self.stage_actions.process_actions_metadata(result['actions'])
                        except Exception as e:
                            logger.error(f"Failed to process stage actions: {e}")

                    # Speak with emotion-based voice modulation (v2.1)
                    # NOTE: Don't set to 'speaking' - let emotion expression show during speech
                    self.voice.speak(response_text, emotion=current_emotion)

                    # Update display
                    if self.arduino_display and self.arduino_display.connected:
                        self.arduino_display.show_conversation(
                            user_text=transcription,
                            gairi_text=response_text,
                            expression='idle',
                            tier=result.get('tier', 'unknown'),
                            response_time=result.get('time_ms', 0) / 1000.0
                        )

                    logger.success(f"✅ Interaction #{self.interaction_count} complete")

                    # Auto-listen for follow-up response (v2.1 - conversational flow)
                    # Multi-turn conversation without re-triggering
                    while True:
                        logger.info("🎤 Listening for follow-up (speak when ready)...")

                        # Set listening expression
                        if self.expression_engine:
                            try:
                                self.expression_engine.set_expression('listening')
                            except:
                                pass

                        # Listen for follow-up (same VAD settings as initial query)
                        # VAD waits for speech, then stops when you stop talking
                        follow_up_audio = self.voice.record_audio_with_vad(
                            max_duration=self.voice.vad_max_duration,  # 30s safety limit
                            silence_duration=self.voice.vad_silence_duration,  # 1.5s after speech
                            vad_aggressiveness=self.voice.vad_aggressiveness
                        )

                        if not follow_up_audio:
                            # No follow-up - end conversation
                            logger.debug("No follow-up detected, conversation complete")
                            break

                        # User has follow-up - process it
                        logger.info("📢 Follow-up detected, continuing conversation...")

                        # Transcribe follow-up
                        follow_up_text = self.voice.transcribe_audio(follow_up_audio, authorization)

                        if not follow_up_text:
                            logger.warning("⚠️ Follow-up transcription failed")
                            break

                        logger.info(f"📝 Follow-up: \"{follow_up_text}\"")

                        # Process follow-up with Gary
                        if self.expression_engine:
                            try:
                                self.expression_engine.set_expression('thinking')
                            except:
                                pass

                        follow_up_result = self.voice.llm_manager.process_audio_query(
                            follow_up_audio, self.voice.sample_rate, authorization
                        )

                        if follow_up_result and follow_up_result.get('response'):
                            follow_up_response = follow_up_result['response']

                            # Get emotion from Gary's response (handle list or string)
                            emotion_data = follow_up_result.get('emotion', 'idle')
                            if isinstance(emotion_data, list) and len(emotion_data) > 0:
                                current_emotion = emotion_data[0]
                                logger.info(f"🎭 Gary returned follow-up emotions: {emotion_data} (using: {current_emotion})")
                            else:
                                current_emotion = emotion_data if isinstance(emotion_data, str) else 'idle'
                                logger.info(f"🎭 Gary returned follow-up emotion: {current_emotion}")

                            # Set visual expression to match emotion (if Gary sent it)
                            if follow_up_result.get('emotion') and self.expression_engine:
                                try:
                                    self.expression_engine.set_expression(follow_up_result['emotion'])
                                    logger.info(f"🎭 Follow-up expression & voice: {current_emotion}")
                                except:
                                    pass

                            # Speak follow-up response with emotion
                            # NOTE: Don't set to 'speaking' - let emotion expression show during speech
                            self.voice.speak(follow_up_response, emotion=current_emotion)

                            # Update display with follow-up
                            if self.arduino_display and self.arduino_display.connected:
                                self.arduino_display.show_conversation(
                                    user_text=follow_up_text,
                                    gairi_text=follow_up_response,
                                    expression='idle',
                                    tier=follow_up_result.get('tier', 'unknown'),
                                    response_time=follow_up_result.get('time_ms', 0) / 1000.0
                                )

                            logger.success("✅ Follow-up complete, listening for next...")
                            # Loop continues to listen for another follow-up
                        else:
                            logger.warning("⚠️ Follow-up processing failed")
                            break
                else:
                    logger.warning("⚠️ Interaction failed - no response")

            except Exception as e:
                logger.error(f"❌ Interaction error: {e}")

                # Show error state on display
                if self.arduino_display and self.arduino_display.connected:
                    self.arduino_display.update_status(
                        state="error",
                        expression="confused"
                    )

            # Return to idle
            if self.expression_engine:
                try:
                    self.expression_engine.set_expression('idle')
                except:
                    pass

        finally:
            # Close servos to release GPIO pins for server access
            if self.servo_controller:
                try:
                    self.servo_controller.close()
                    self.servo_controller = None
                    logger.debug("Servos closed (GPIO released for server)")
                except Exception as e:
                    logger.debug(f"Servo close failed: {e}")

            # Close Arduino display to release serial port for server access
            if self.arduino_display and self.arduino_display.connected:
                try:
                    self.arduino_display.close()
                    logger.debug("Arduino display closed (serial port released for server)")
                except Exception as e:
                    logger.debug(f"Arduino display close failed: {e}")

            # ALWAYS release hardware lock (even if exception occurs)
            coordinator.release()

            # Mark interaction complete and update timestamp
            self.in_interaction = False
            self.last_interaction_time = time.time()
            logger.info(f"✅ Interaction #{self.interaction_count} complete - System ready for next trigger")

    async def _check_special_command(self, transcription: str) -> bool:
        """
        Check and handle special voice commands (Tim-only)

        Args:
            transcription: Transcribed user query

        Returns:
            True if special command was handled, False otherwise
        """
        transcription_lower = transcription.lower()

        # Face enrollment command
        if any(phrase in transcription_lower for phrase in [
            'register new face',
            'add new face',
            'enroll new face',
            'add a new face',
            'register a face',
            'add new user',
            'register new person',
            'add new person'
        ]):
            logger.info("🎯 Face enrollment command detected (Tim authorized)")
            await self.enroll_new_face()
            return True

        # No special command detected
        return False

    async def enroll_new_face(self):
        """
        Voice-guided face enrollment flow (Tim-only)

        Flow:
        1. Ask for name
        2. Collect 20 face photos
        3. Register as guest (Level 2)
        4. Confirm enrollment
        """
        try:
            logger.info("=" * 60)
            logger.info("FACE ENROLLMENT MODE")
            logger.info("=" * 60)

            # Step 1: Get name via voice
            if self.expression_engine:
                try:
                    self.expression_engine.set_expression('listening')
                except:
                    pass

            self.voice.speak("What is the person's name?")
            logger.info("🎤 Listening for name...")

            # Record name
            audio = self.voice.record_audio_with_vad(
                max_duration=10.0,
                silence_duration=1.5
            )

            if audio is None:
                self.voice.speak("Sorry, I didn't hear a name. Enrollment cancelled.")
                logger.warning("No audio recorded for name")
                return

            # Transcribe name
            name = self.voice.transcribe_audio(audio)
            if not name or len(name.strip()) == 0:
                self.voice.speak("Sorry, I didn't understand the name. Enrollment cancelled.")
                logger.warning("Name transcription failed")
                return

            # Clean up name (remove punctuation, lowercase)
            name = name.strip().lower().replace(' ', '_')
            name = ''.join(c for c in name if c.isalnum() or c == '_')

            logger.info(f"📝 Name captured: {name}")

            # Confirm name
            self.voice.speak(f"Okay, registering {name}. Please have them look at the camera.")
            await asyncio.sleep(1)

            # Step 2: Collect photos
            if self.expression_engine:
                try:
                    self.expression_engine.set_expression('alert')
                except:
                    pass

            # Update display
            if self.arduino_display and self.arduino_display.connected:
                self.arduino_display.update_status(
                    state="enrolling",
                    expression="alert",
                    user=name,
                    level=2,
                    confidence=0.0
                )

            logger.info(f"📸 Starting photo collection for {name}...")
            self.voice.speak("Starting photo collection. Please look at the camera and move your head through different angles.")

            # Run photo collection script
            from pathlib import Path
            import subprocess

            output_dir = Path(f"/home/tim/GairiHead/data/known_faces/{name}")

            # Run headless collection
            result = subprocess.run(
                [
                    'python3',
                    '/home/tim/GairiHead/scripts/collect_face_photos_headless.py',
                    name,
                    '--num-photos', '20',
                    '--interval', '2.0'
                ],
                capture_output=True,
                text=True,
                timeout=120  # 2 minutes max
            )

            if result.returncode == 0:
                logger.success(f"✅ Face photos collected for {name}")

                # Step 3: Update metadata for Level 2 (Guest)
                import json
                metadata_file = output_dir / "metadata.json"
                if metadata_file.exists():
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                    metadata['authorization_level'] = 2  # Guest
                    metadata['description'] = "Guest user"
                    metadata['enrolled_by'] = "tim"
                    metadata['enrollment_method'] = "voice_authorized"
                    with open(metadata_file, 'w') as f:
                        json.dump(metadata, f, indent=2)

                # Step 4: Confirm
                if self.expression_engine:
                    try:
                        self.expression_engine.set_expression('happy')
                    except:
                        pass

                self.voice.speak(f"Success! {name} has been registered as a guest. They now have Level 2 access.")
                logger.success(f"✅ {name} enrolled successfully as Level 2 (Guest)")

                # Update display
                if self.arduino_display and self.arduino_display.connected:
                    self.arduino_display.show_conversation(
                        user_text=f"Register {name}",
                        gairi_text=f"✅ {name} registered as guest (Level 2)",
                        expression="happy",
                        tier="local",
                        response_time=0.0
                    )

            else:
                logger.error(f"❌ Photo collection failed: {result.stderr}")
                self.voice.speak(f"Sorry, photo collection failed. Please try again.")

                if self.expression_engine:
                    try:
                        self.expression_engine.set_expression('confused')
                    except:
                        pass

        except subprocess.TimeoutExpired:
            logger.error("❌ Face enrollment timed out")
            self.voice.speak("Enrollment took too long. Please try again.")
        except Exception as e:
            logger.error(f"❌ Face enrollment error: {e}")
            self.voice.speak("Sorry, enrollment failed due to an error.")

    async def run_interactive_mode(self):
        """
        Run in interactive mode (press Enter to trigger interaction)

        This is the simple "do it well" mode - button triggered instead of
        continuous listening with wake words (Core Principle #8)
        """
        logger.info("\n" + "=" * 60)
        logger.info("GairiHead Voice Assistant - Interactive Mode")
        logger.info("=" * 60)
        logger.info("Press ENTER to trigger voice interaction")
        logger.info("Press Ctrl+C to exit")
        logger.info("=" * 60 + "\n")

        self.running = True

        try:
            while self.running:
                # Wait for Enter key
                await asyncio.get_event_loop().run_in_executor(
                    None, input, "\nPress ENTER to start interaction... "
                )

                # Handle interaction
                await self.handle_interaction()

        except KeyboardInterrupt:
            logger.info("\n\nShutting down...")
            self.running = False

    async def run_production_mode(self):
        """
        Run in production mode (touchscreen trigger, no keyboard)

        Listens for Arduino touchscreen center button press to trigger interaction.
        Perfect for deployed GairiHead (no keyboard available).
        """
        logger.info("\n" + "=" * 60)
        logger.info("GairiHead Voice Assistant - Production Mode")
        logger.info("=" * 60)
        logger.info("Touch CENTER button on display to trigger voice interaction")
        logger.info("Press Ctrl+C to exit")
        logger.info("=" * 60 + "\n")

        if not self.arduino_display or not self.arduino_display.connected:
            logger.error("❌ Arduino display not connected - production mode requires touchscreen!")
            logger.info("   Run with --mode interactive for keyboard-based testing")
            return

        # Set initial idle state on display
        if self.arduino_display and self.arduino_display.connected:
            self.arduino_display.update_status(
                state="idle",
                expression="idle",
                user="ready",
                level=3,
                confidence=0.0
            )

        # Set initial idle expression
        if self.expression_engine:
            try:
                self.expression_engine.set_expression('idle')
            except:
                pass

        self.running = True

        try:
            while self.running:
                # Reconnect Arduino if needed (after server released it)
                if not self.arduino_display or not self.arduino_display.connected:
                    try:
                        display_config = self.config.get('hardware', {}).get('arduino_display', {})
                        # Preserve last conversation from previous instance
                        last_conv = self.arduino_display.last_conversation if self.arduino_display else None

                        self.arduino_display = ArduinoDisplay(
                            port=display_config.get('port', '/dev/ttyACM0'),
                            baudrate=display_config.get('baudrate', 115200),
                            enabled=True
                        )
                        if self.arduino_display.connected:
                            logger.debug("Arduino display reconnected")

                            # Restore last conversation if available
                            if last_conv:
                                self.arduino_display.last_conversation = last_conv
                                self.arduino_display.restore_last_conversation()
                            else:
                                # No conversation to restore, just show idle state
                                self.arduino_display.update_status(
                                    state="idle",
                                    expression="idle",
                                    user="ready",
                                    level=3,
                                    confidence=0.0
                                )
                    except Exception as e:
                        logger.debug(f"Arduino reconnect failed: {e}")
                        await asyncio.sleep(1.0)  # Wait before retry
                        continue

                # Check for touch commands from Arduino
                cmd = self.arduino_display.check_commands()

                if cmd:
                    logger.debug(f"📥 Arduino command received: {cmd}")
                    if cmd.get('touch') == 'center':
                        logger.info("🖱️ Center button pressed - starting interaction")
                        await self.handle_interaction()
                    else:
                        logger.warning(f"⚠️ Unknown Arduino command: {cmd}")

                # Small delay to avoid CPU spinning
                await asyncio.sleep(0.1)

        except KeyboardInterrupt:
            logger.info("\n\nShutting down...")
            self.running = False
    
    async def run_continuous_mode(self, interval: float = 5.0):
        """
        Run in continuous mode (auto-trigger at intervals for testing)
        
        Args:
            interval: Seconds between interactions
        """
        logger.info("\n" + "=" * 60)
        logger.info("GairiHead Voice Assistant - Continuous Mode")
        logger.info("=" * 60)
        logger.info(f"Auto-triggering every {interval} seconds")
        logger.info("Press Ctrl+C to exit")
        logger.info("=" * 60 + "\n")
        
        self.running = True
        
        try:
            while self.running:
                await self.handle_interaction()
                
                # Wait before next interaction
                logger.info(f"Waiting {interval} seconds before next interaction...")
                await asyncio.sleep(interval)
        
        except KeyboardInterrupt:
            logger.info("\n\nShutting down...")
            self.running = False
    
    def get_stats(self) -> dict:
        """Get usage statistics"""
        stats = {
            'total_interactions': self.interaction_count,
            'voice_stats': self.voice.get_stats() if self.voice else {},
            'components': {
                'camera': self.camera is not None,
                'vision': self.vision is not None,
                'llm': self.llm_manager is not None,
                'voice': self.voice is not None
            }
        }
        return stats
    
    def shutdown(self):
        """Clean shutdown of all components"""
        logger.info("Shutting down GairiHead...")

        if self.camera:
            self.camera.release()

        if hasattr(self, 'servo_controller') and self.servo_controller:
            try:
                self.servo_controller.cleanup()
                logger.debug("Servo controller cleaned up")
            except:
                pass

        logger.info("✅ Shutdown complete")


async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="GairiHead Voice Assistant")
    parser.add_argument(
        '--mode',
        choices=['interactive', 'production', 'continuous', 'test'],
        default='production',
        help='Run mode: production (touchscreen), interactive (keyboard), continuous (auto), or test (component tests)'
    )
    parser.add_argument(
        '--interval',
        type=float,
        default=5.0,
        help='Interval for continuous mode (seconds)'
    )
    parser.add_argument(
        '--config',
        type=str,
        default='config/gairi_head.yaml',
        help='Config file path'
    )
    
    args = parser.parse_args()
    
    # Configure logging
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    logger.add(
        "logs/gairi_head_{time:YYYY-MM-DD}.log",
        rotation="1 day",
        retention="30 days",
        level="DEBUG"
    )
    
    # Initialize assistant
    config_path = Path(__file__).parent / args.config
    assistant = GairiHeadAssistant(config_path)
    
    if not await assistant.initialize():
        logger.error("Failed to initialize GairiHead - exiting")
        return 1
    
    # Run based on mode
    try:
        if args.mode == 'test':
            logger.info("Running component tests...")

            # Test voice pipeline
            logger.info("\n=== Testing Voice Pipeline ===")
            assistant.voice.test_pipeline()

            # Show stats
            logger.info("\n=== Statistics ===")
            stats = assistant.get_stats()
            for key, value in stats.items():
                logger.info(f"{key}: {value}")

        elif args.mode == 'continuous':
            await assistant.run_continuous_mode(interval=args.interval)

        elif args.mode == 'interactive':
            await assistant.run_interactive_mode()

        else:  # production (default)
            await assistant.run_production_mode()
    
    finally:
        assistant.shutdown()
        
        # Show final stats
        logger.info("\n=== Final Statistics ===")
        stats = assistant.get_stats()
        logger.info(f"Total interactions: {stats['total_interactions']}")
        if stats['voice_stats']:
            for key, value in stats['voice_stats'].items():
                logger.info(f"  {key}: {value}")
    
    return 0


if __name__ == '__main__':
    sys.exit(asyncio.run(main()))
