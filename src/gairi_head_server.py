"""
GairiHead Websocket Server
Allows main Gary agent to request camera snapshots, audio, and vision analysis

Commands from main Gary:
- capture_snapshot: Return base64 encoded camera frame
- record_audio: Record N seconds of audio, return base64 WAV
- analyze_scene: Capture frame + describe what's happening
- detect_faces: Fast face detection without full image
- get_status: Return GairiHead status (camera, servos, expression)
- set_expression: Change facial expression (servos)
- speak: Make GairiHead speak text with mouth animation and optional expression
"""

import asyncio
import json
import base64
import io
import time
import os
import signal
import sys
from pathlib import Path
from typing import Optional, Dict, Any, Set
from collections import defaultdict, deque
import websockets
from loguru import logger
import yaml
import numpy as np
import cv2

# Audio recording
import sounddevice as sd
import soundfile as sf


# =============================================================================
# RATE LIMITER
# =============================================================================

class RateLimiter:
    """
    Rate limiter for WebSocket connections
    Tracks requests per connection and enforces limits
    """

    def __init__(self, requests_per_minute: int = 30, window_seconds: int = 60):
        """
        Initialize rate limiter

        Args:
            requests_per_minute: Maximum requests allowed per minute per connection
            window_seconds: Time window for tracking requests (default 60s)
        """
        self.requests_per_minute = requests_per_minute
        self.window_seconds = window_seconds

        # Track request timestamps per connection
        # Key: connection ID, Value: deque of request timestamps
        self.request_history: Dict[Any, deque] = defaultdict(lambda: deque())

        # Track violations per connection (for exponential backoff)
        self.violations: Dict[Any, int] = defaultdict(int)

        logger.info(f"⏱️  Rate limiter initialized: {requests_per_minute} requests/minute")

    def check_rate_limit(self, connection_id: Any) -> tuple[bool, Optional[str]]:
        """
        Check if connection has exceeded rate limit

        Args:
            connection_id: Unique identifier for the connection

        Returns:
            Tuple of (allowed: bool, error_message: Optional[str])
        """
        now = time.time()

        # Get request history for this connection
        history = self.request_history[connection_id]

        # Remove requests outside the time window
        while history and history[0] < now - self.window_seconds:
            history.popleft()

        # Check if limit exceeded
        if len(history) >= self.requests_per_minute:
            # Rate limit exceeded
            self.violations[connection_id] += 1
            violation_count = self.violations[connection_id]

            # Calculate backoff time (exponential)
            backoff_seconds = min(300, 10 * (2 ** (violation_count - 1)))  # Max 5 minutes

            logger.warning(
                f"🚫 Rate limit exceeded for {connection_id}: "
                f"{len(history)} requests in {self.window_seconds}s "
                f"(violation #{violation_count}, backoff: {backoff_seconds}s)"
            )

            error_msg = (
                f"Rate limit exceeded: {self.requests_per_minute} requests per minute. "
                f"Please wait {backoff_seconds} seconds before retrying."
            )
            return False, error_msg

        # Allowed - record this request
        history.append(now)
        return True, None

    def cleanup_connection(self, connection_id: Any):
        """Remove tracking data for a disconnected connection"""
        if connection_id in self.request_history:
            del self.request_history[connection_id]
        if connection_id in self.violations:
            del self.violations[connection_id]


# =============================================================================
# GAIRIHEAD SERVER
# =============================================================================

class GairiHeadServer:
    """Websocket server for GairiHead remote control"""

    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 8766,
        config_path: Optional[Path] = None
    ):
        """
        Initialize GairiHead server

        Args:
            host: Listen address (0.0.0.0 = all interfaces)
            port: Listen port (8766 for GairiHead, 8765 is main Gary)
            config_path: Path to gairi_head.yaml
        """
        self.host = host
        self.port = port

        # Load config
        if config_path is None:
            config_path = Path(__file__).parent.parent / 'config' / 'gairi_head.yaml'

        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        # Security: API token authentication
        # Token can be set via environment variable or config file
        self.api_token = os.environ.get('GAIRIHEAD_API_TOKEN')
        if not self.api_token:
            # Try to load from config
            self.api_token = self.config.get('server', {}).get('api_token')

        if self.api_token:
            logger.info("🔒 WebSocket authentication enabled")
        else:
            logger.warning("⚠️  No API token configured - authentication disabled (INSECURE!)")

        # Hardware managers (lazy init)
        self.camera_manager = None
        self.servo_controller = None
        self.arduino_display = None
        self.voice_handler = None
        self.expression_engine = None

        # Connection management
        self.active_connections: Set[websockets.WebSocketServerProtocol] = set()
        self.max_connections = 10  # Moderate limit

        # Rate limiting
        self.rate_limiter = RateLimiter(requests_per_minute=30, window_seconds=60)

        # Status
        self.is_running = False
        self.current_expression = "idle"

        logger.info(f"GairiHead server initialized on {host}:{port}")
        logger.info(f"🔒 Max concurrent connections: {self.max_connections}")

    def _get_camera(self):
        """Lazy init camera manager"""
        if self.camera_manager is None:
            from camera_manager import CameraManager
            self.camera_manager = CameraManager()
            logger.info("Camera manager initialized")
        return self.camera_manager

    def _get_servos(self):
        """Lazy init servo controller"""
        if self.servo_controller is None:
            try:
                from servo_controller import ServoController
                self.servo_controller = ServoController()
                logger.info("Servo controller initialized")
            except Exception as e:
                if "GPIO busy" in str(e) or "busy" in str(e).lower():
                    logger.warning("Servos in use by main app (GPIO busy)")
                    raise RuntimeError("Servos currently in use by main app")
                else:
                    raise
        return self.servo_controller

    def _get_arduino_display(self):
        """Lazy init Arduino display"""
        if self.arduino_display is None:
            try:
                from arduino_display import ArduinoDisplay
                # Try to connect to Arduino (USB connection)
                hardware_config = self.config.get('hardware', {})
                display_config = hardware_config.get('arduino_display', {})
                port = display_config.get('port', '/dev/ttyACM0')
                enabled = display_config.get('enabled', True)
                self.arduino_display = ArduinoDisplay(port=port, enabled=enabled)
                if self.arduino_display.connected:
                    logger.info("Arduino display initialized")
                else:
                    logger.warning("Arduino display not connected")
            except Exception as e:
                logger.warning(f"Arduino display initialization failed: {e}")
                # Create disabled instance to prevent repeated init attempts
                from arduino_display import ArduinoDisplay
                self.arduino_display = ArduinoDisplay(enabled=False)
        return self.arduino_display

    def _get_voice_handler(self):
        """Lazy init voice handler"""
        if self.voice_handler is None:
            from voice_handler import VoiceHandler
            self.voice_handler = VoiceHandler(self.config)
            logger.info("Voice handler initialized")
        return self.voice_handler

    def _get_expression_engine(self):
        """Lazy init expression engine"""
        if self.expression_engine is None:
            from expression_engine import ExpressionEngine
            from pathlib import Path

            # ExpressionEngine expects config directory path
            config_dir = Path(__file__).parent.parent / 'config'

            # Create expression engine
            self.expression_engine = ExpressionEngine(config_path=str(config_dir))

            # Attach servo controller and display
            servos = self._get_servos()
            display = self._get_arduino_display()
            self.expression_engine.set_controllers(
                servo_controller=servos,
                arduino_display=display
            )

            logger.info("Expression engine initialized")
        return self.expression_engine

    # Allowed actions (whitelist)
    ALLOWED_ACTIONS = {
        'capture_snapshot', 'record_audio', 'analyze_scene', 'get_status',
        'set_expression', 'detect_faces', 'speak', 'blink', 'test_sync'
    }

    def _validate_command(self, command: Dict[str, Any]) -> Optional[str]:
        """
        Validate command structure and parameters

        Args:
            command: Command dict to validate

        Returns:
            Error message if invalid, None if valid
        """
        # Check action exists
        action = command.get('action')
        if not action:
            return "Missing required field: 'action'"

        # Check action is string
        if not isinstance(action, str):
            return "Field 'action' must be a string"

        # Check action is in whitelist
        if action not in self.ALLOWED_ACTIONS:
            return f"Unknown action: {action}. Allowed: {', '.join(sorted(self.ALLOWED_ACTIONS))}"

        # Validate params
        params = command.get('params', {})
        if not isinstance(params, dict):
            return "Field 'params' must be a dictionary"

        # Action-specific validation
        if action == 'speak':
            text = params.get('text')
            if not text:
                return "Missing required parameter 'text' for speak action"
            if not isinstance(text, str):
                return "Parameter 'text' must be a string"
            if len(text) > 5000:  # Max 5000 characters
                return "Parameter 'text' exceeds maximum length (5000 characters)"

        elif action == 'set_expression':
            expression = params.get('expression')
            if not expression:
                return "Missing required parameter 'expression' for set_expression action"
            if not isinstance(expression, str):
                return "Parameter 'expression' must be a string"
            if len(expression) > 50:
                return "Parameter 'expression' too long (max 50 characters)"

        elif action == 'record_audio':
            duration = params.get('duration', 3)
            if not isinstance(duration, (int, float)):
                return "Parameter 'duration' must be a number"
            if duration < 0.1 or duration > 60:
                return "Parameter 'duration' must be between 0.1 and 60 seconds"

        elif action == 'capture_snapshot':
            quality = params.get('quality', 85)
            if not isinstance(quality, int):
                return "Parameter 'quality' must be an integer"
            if quality < 1 or quality > 100:
                return "Parameter 'quality' must be between 1 and 100"

        return None  # Valid

    async def handle_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle incoming command from main Gary

        Args:
            command: Dict with 'action' and optional params

        Returns:
            Response dict with 'status', 'data', and optional 'error'
        """
        # Validate command
        validation_error = self._validate_command(command)
        if validation_error:
            logger.warning(f"Invalid command: {validation_error}")
            return {
                'status': 'error',
                'error': validation_error
            }

        action = command.get('action')
        params = command.get('params', {})

        logger.info(f"Received command: {action}")

        try:
            # Route to handler
            if action == 'capture_snapshot':
                return await self._handle_capture_snapshot(params)

            elif action == 'record_audio':
                return await self._handle_record_audio(params)

            elif action == 'analyze_scene':
                return await self._handle_analyze_scene(params)

            elif action == 'get_status':
                return await self._handle_get_status(params)

            elif action == 'set_expression':
                return await self._handle_set_expression(params)

            elif action == 'detect_faces':
                return await self._handle_detect_faces(params)

            elif action == 'speak':
                return await self._handle_speak(params)

            elif action == 'blink':
                return await self._handle_blink(params)

            elif action == 'test_sync':
                return await self._handle_test_sync(params)

            else:
                # Should never reach here due to validation
                return {
                    'status': 'error',
                    'error': f'Unknown action: {action}'
                }

        except Exception as e:
            logger.error(f"Error handling command {action}: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }

    async def _handle_capture_snapshot(self, params: Dict) -> Dict:
        """Capture single camera frame, return as base64 JPEG"""
        logger.info("Capturing snapshot...")

        cam = self._get_camera()
        ret, frame = cam.read_frame()

        if not ret or frame is None:
            return {
                'status': 'error',
                'error': 'Failed to capture frame'
            }

        # Encode as JPEG
        quality = params.get('quality', 85)
        _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, quality])

        # Convert to base64
        img_base64 = base64.b64encode(buffer).decode('utf-8')

        return {
            'status': 'success',
            'data': {
                'image': img_base64,
                'format': 'jpeg',
                'width': frame.shape[1],
                'height': frame.shape[0],
                'timestamp': time.time()
            }
        }

    async def _handle_record_audio(self, params: Dict) -> Dict:
        """Record audio from mic, return as base64 WAV"""
        duration = params.get('duration', 3)  # seconds
        sample_rate = params.get('sample_rate', 16000)

        logger.info(f"Recording audio for {duration}s...")

        # Get mic config
        mic_config = self.config['voice']['microphone']
        device_index = mic_config.get('device_index', None)

        # Record audio
        try:
            recording = sd.rec(
                int(duration * sample_rate),
                samplerate=sample_rate,
                channels=1,
                device=device_index,
                dtype='int16'
            )
            sd.wait()  # Wait for recording to complete

            # Convert to WAV bytes
            wav_buffer = io.BytesIO()
            sf.write(wav_buffer, recording, sample_rate, format='WAV', subtype='PCM_16')
            wav_buffer.seek(0)

            # Convert to base64
            audio_base64 = base64.b64encode(wav_buffer.read()).decode('utf-8')

            return {
                'status': 'success',
                'data': {
                    'audio': audio_base64,
                    'format': 'wav',
                    'duration': duration,
                    'sample_rate': sample_rate,
                    'timestamp': time.time()
                }
            }

        except Exception as e:
            return {
                'status': 'error',
                'error': f'Audio recording failed: {e}'
            }

    async def _handle_analyze_scene(self, params: Dict) -> Dict:
        """
        Capture frame + basic analysis (face detection, etc.)
        Main Gary will do deeper analysis with Claude Vision
        """
        logger.info("Analyzing scene...")

        # Capture frame
        cam = self._get_camera()
        ret, frame = cam.read_frame()

        if not ret or frame is None:
            return {
                'status': 'error',
                'error': 'Failed to capture frame'
            }

        # Basic face detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        face_cascade = cv2.CascadeClassifier(cascade_path)
        faces = face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(30, 30))

        # Encode frame
        _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        img_base64 = base64.b64encode(buffer).decode('utf-8')

        return {
            'status': 'success',
            'data': {
                'image': img_base64,
                'format': 'jpeg',
                'faces_detected': len(faces),
                'face_locations': [
                    {'x': int(x), 'y': int(y), 'w': int(w), 'h': int(h)}
                    for x, y, w, h in faces
                ],
                'timestamp': time.time()
            }
        }

    async def _handle_detect_faces(self, params: Dict) -> Dict:
        """Fast face detection without returning full image"""
        logger.info("Detecting faces...")

        cam = self._get_camera()
        ret, frame = cam.read_frame()

        if not ret or frame is None:
            return {
                'status': 'error',
                'error': 'Failed to capture frame'
            }

        # Face detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        face_cascade = cv2.CascadeClassifier(cascade_path)
        faces = face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(30, 30))

        return {
            'status': 'success',
            'data': {
                'faces_detected': len(faces),
                'face_locations': [
                    {'x': int(x), 'y': int(y), 'w': int(w), 'h': int(h)}
                    for x, y, w, h in faces
                ],
                'timestamp': time.time()
            }
        }

    async def _handle_get_status(self, params: Dict) -> Dict:
        """Get GairiHead current status"""
        logger.info("Getting status...")

        # Check hardware availability without locking devices
        # (main app may have them open)
        import os

        # Check camera: Look for video devices
        camera_available = (
            os.path.exists('/dev/video0') or
            os.path.exists('/dev/video1') or
            os.path.exists('/dev/video2')
        )

        # Check servos: Verify GPIO access
        servos_available = os.path.exists('/dev/gpiomem') or os.path.exists('/dev/gpiochip0')

        status = {
            'expression': self.current_expression,
            'camera_available': camera_available,
            'servos_available': servos_available,
            'server_uptime': time.time(),
            'timestamp': time.time(),
            'note': 'Hardware may be in use by main app'
        }

        # If camera is already initialized by server, get info
        if self.camera_manager:
            try:
                cam_info = self.camera_manager.get_info()
                status['camera'] = cam_info
            except:
                pass

        return {
            'status': 'success',
            'data': status
        }

    async def _handle_set_expression(self, params: Dict) -> Dict:
        """Set facial expression"""
        expression = params.get('expression', 'idle')
        logger.info(f"Setting expression (Gary remote): {expression}")

        try:
            # Acquire hardware lock (remote = high priority)
            from hardware_coordinator import get_coordinator
            coordinator = get_coordinator()

            if not coordinator.acquire(timeout=5.0, is_remote=True):
                return {
                    'status': 'error',
                    'error': 'Hardware busy - could not acquire lock'
                }

            try:
                servos = self._get_servos()
                servos.set_expression(expression)
                self.current_expression = expression

                # Update Arduino display with new expression
                display = self._get_arduino_display()
                if display and display.connected:
                    display.update_status(
                        user=params.get('user', 'Gary'),
                        level=params.get('level', 1),
                        state=params.get('state', 'idle'),
                        confidence=params.get('confidence', 1.0),
                        expression=expression
                    )

                return {
                    'status': 'success',
                    'data': {
                        'expression': expression,
                        'timestamp': time.time()
                    }
                }

            finally:
                # Always release hardware lock
                coordinator.release()

        except Exception as e:
            return {
                'status': 'error',
                'error': f'Failed to set expression: {e}'
            }

    async def _handle_speak(self, params: Dict) -> Dict:
        """Make GairiHead speak text with optional expression and mouth animation"""
        text = params.get('text', '')
        expression = params.get('expression', None)  # Optional expression during speech
        animate_mouth = params.get('animate_mouth', True)  # Default to animating mouth

        if not text:
            return {
                'status': 'error',
                'error': 'No text provided to speak'
            }

        logger.info(f"Speaking (Gary remote): {text[:50]}{'...' if len(text) > 50 else ''}")

        try:
            # Acquire hardware lock (remote = high priority)
            from hardware_coordinator import get_coordinator
            coordinator = get_coordinator()

            if not coordinator.acquire(timeout=10.0, is_remote=True):
                return {
                    'status': 'error',
                    'error': 'Hardware busy - could not acquire lock'
                }

            try:
                # Get voice handler and expression engine
                voice = self._get_voice_handler()
                expr_engine = self._get_expression_engine()

                # Set expression if provided
                if expression:
                    servos = self._get_servos()
                    servos.set_expression(expression)
                    self.current_expression = expression

                # Update Arduino display with "speaking" state
                display = self._get_arduino_display()
                if display and display.connected:
                    # Show what Gary is saying on the display
                    display.show_conversation(
                        user_text="",  # No user query in remote mode
                        gairi_text=text,
                        expression=expression or self.current_expression,
                        tier="gary",  # Show it's from Gary
                        response_time=0.0
                    )

                # Speak with mouth animation
                # Voice handler automatically animates mouth if expression_engine is set
                voice.expression_engine = expr_engine
                voice.speak(text)

                # Return display to idle state after speaking
                if display and display.connected:
                    display.update_status(
                        user="ready",
                        level=3,
                        state="idle",
                        confidence=0.0,
                        expression=self.current_expression
                    )

                return {
                    'status': 'success',
                    'data': {
                        'text': text,
                        'expression': expression or self.current_expression,
                        'animated_mouth': animate_mouth,
                        'timestamp': time.time()
                    }
                }

            finally:
                # Close Arduino display to release serial port for main.py
                if self.arduino_display and self.arduino_display.connected:
                    try:
                        self.arduino_display.close()
                        self.arduino_display = None  # Force reconnect on next use
                        logger.debug("Arduino display closed (serial port released)")
                    except Exception as e:
                        logger.debug(f"Arduino display close failed: {e}")

                # Always release hardware lock
                coordinator.release()

        except Exception as e:
            logger.error(f"Failed to speak: {e}")
            return {
                'status': 'error',
                'error': f'Failed to speak: {e}'
            }

    async def _handle_blink(self, params: Dict) -> Dict:
        """Make GairiHead blink with optional repeat count"""
        count = params.get('count', 1)  # Number of blinks, default 1
        duration = params.get('duration', None)  # Blink duration, None for natural
        natural_variation = params.get('natural_variation', True)

        logger.info(f"Blinking (Gary remote): {count} time{'s' if count > 1 else ''}")

        try:
            # Acquire hardware lock (remote = high priority)
            from hardware_coordinator import get_coordinator
            coordinator = get_coordinator()

            if not coordinator.acquire(timeout=5.0, is_remote=True):
                return {
                    'status': 'error',
                    'error': 'Hardware busy - could not acquire lock'
                }

            try:
                servos = self._get_servos()

                # Perform blinks
                for i in range(count):
                    servos.blink(duration=duration, natural_variation=natural_variation)
                    # Small pause between blinks if multiple
                    if count > 1 and i < count - 1:
                        await asyncio.sleep(0.3)

                return {
                    'status': 'success',
                    'data': {
                        'blinks': count,
                        'timestamp': time.time()
                    }
                }

            finally:
                # Always release hardware lock
                coordinator.release()

        except Exception as e:
            logger.error(f"Failed to blink: {e}")
            return {
                'status': 'error',
                'error': f'Failed to blink: {e}'
            }

    async def _handle_test_sync(self, params: Dict) -> Dict:
        """Test synchronized eye movement: full open → pause → full closed → pause → full open"""
        logger.info("Running sync test: full open → close → open with 2s pauses")

        try:
            # Acquire hardware lock (remote = high priority)
            from hardware_coordinator import get_coordinator
            coordinator = get_coordinator()

            if not coordinator.acquire(timeout=5.0, is_remote=True):
                return {
                    'status': 'error',
                    'error': 'Hardware busy - could not acquire lock'
                }

            try:
                servos = self._get_servos()

                # Run the test sequence
                servos.test_sync_movement()

                return {
                    'status': 'success',
                    'data': {
                        'test': 'sync_movement_complete',
                        'timestamp': time.time()
                    }
                }

            finally:
                # Always release hardware lock
                coordinator.release()

        except Exception as e:
            logger.error(f"Failed to run sync test: {e}")
            return {
                'status': 'error',
                'error': f'Failed to run sync test: {e}'
            }

    async def handle_client(self, websocket):
        """Handle websocket client connection"""
        client_addr = websocket.remote_address
        logger.info(f"Client connected: {client_addr}")

        # Connection limit check
        if len(self.active_connections) >= self.max_connections:
            logger.warning(f"🚫 Connection limit reached ({self.max_connections}), rejecting {client_addr}")
            try:
                await websocket.send(json.dumps({
                    'status': 'error',
                    'error': f'Server connection limit reached ({self.max_connections} active connections). Please try again later.'
                }))
                await websocket.close()
            except:
                pass
            return

        # Add to active connections
        self.active_connections.add(websocket)
        logger.debug(f"Active connections: {len(self.active_connections)}")

        try:
            # Authentication check
            authenticated = False
            if self.api_token:
                # Require authentication
                try:
                    # Wait for auth message (first message must be auth)
                    auth_message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    auth_data = json.loads(auth_message)

                    # Check token
                    provided_token = auth_data.get('token')
                    if provided_token == self.api_token:
                        authenticated = True
                        logger.info(f"✅ Client authenticated: {client_addr}")
                        # Send auth success
                        await websocket.send(json.dumps({
                            'status': 'authenticated',
                            'message': 'Authentication successful'
                        }))
                    else:
                        logger.warning(f"🚫 Authentication failed for {client_addr}: Invalid token")
                        await websocket.send(json.dumps({
                            'status': 'error',
                            'error': 'Authentication failed: Invalid token'
                        }))
                        await websocket.close()
                        return

                except (asyncio.TimeoutError, json.JSONDecodeError, KeyError):
                    logger.warning(f"🚫 Authentication failed for {client_addr}: Invalid auth message")
                    await websocket.send(json.dumps({
                        'status': 'error',
                        'error': 'Authentication failed: Invalid auth message'
                    }))
                    await websocket.close()
                    return
            else:
                # No token configured - allow all connections (insecure)
                authenticated = True

            # Main message loop (only reached if authenticated)
            async for message in websocket:
                # Rate limiting check
                allowed, error_msg = self.rate_limiter.check_rate_limit(client_addr)
                if not allowed:
                    response = {
                        'status': 'error',
                        'error': error_msg
                    }
                    await websocket.send(json.dumps(response))
                    continue

                # Parse command
                try:
                    command = json.loads(message)
                except json.JSONDecodeError as e:
                    response = {
                        'status': 'error',
                        'error': f'Invalid JSON: {e}'
                    }
                    await websocket.send(json.dumps(response))
                    continue

                # Handle command
                response = await self.handle_command(command)

                # Send response
                await websocket.send(json.dumps(response))

        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Client disconnected: {client_addr}")
        except Exception as e:
            logger.error(f"Error handling client {client_addr}: {e}")
        finally:
            # Clean up connection tracking
            self.active_connections.discard(websocket)
            self.rate_limiter.cleanup_connection(client_addr)
            logger.debug(f"Connection cleaned up. Active connections: {len(self.active_connections)}")

    async def start(self):
        """Start websocket server"""
        logger.info(f"Starting GairiHead server on ws://{self.host}:{self.port}")

        self.is_running = True

        async with websockets.serve(self.handle_client, self.host, self.port):
            logger.success(f"✅ GairiHead server running on ws://{self.host}:{self.port}")
            await asyncio.Future()  # Run forever

    def cleanup(self):
        """Clean up resources with timeout protection"""
        logger.info("Starting resource cleanup...")

        # Camera cleanup
        if self.camera_manager is not None:
            try:
                self.camera_manager.release()
                logger.debug("✓ Camera released")
            except Exception as e:
                logger.warning(f"Camera cleanup error: {e}")

        # Servo controller cleanup
        if self.servo_controller is not None:
            try:
                self.servo_controller.cleanup()
                logger.debug("✓ Servos cleaned up")
            except Exception as e:
                logger.warning(f"Servo cleanup error: {e}")

        # Arduino display cleanup
        if self.arduino_display is not None:
            try:
                if hasattr(self.arduino_display, 'connected') and self.arduino_display.connected:
                    self.arduino_display.close()
                logger.debug("✓ Arduino display closed")
            except Exception as e:
                logger.warning(f"Arduino cleanup error: {e}")

        # Voice handler cleanup
        if self.voice_handler is not None:
            try:
                # Voice handler cleanup (if method exists)
                if hasattr(self.voice_handler, 'cleanup'):
                    self.voice_handler.cleanup()
                logger.debug("✓ Voice handler cleaned up")
            except Exception as e:
                logger.warning(f"Voice handler cleanup error: {e}")

        # Expression engine cleanup (already cleans up servos)
        if self.expression_engine is not None:
            try:
                if hasattr(self.expression_engine, 'cleanup'):
                    self.expression_engine.cleanup()
                logger.debug("✓ Expression engine cleaned up")
            except Exception as e:
                logger.warning(f"Expression engine cleanup error: {e}")

        logger.success("✅ GairiHead server cleaned up")

    async def shutdown_gracefully(self):
        """
        Gracefully shutdown server
        1. Stop accepting new connections
        2. Close active websocket connections
        3. Cleanup resources
        4. Exit
        """
        logger.info("🛑 Graceful shutdown initiated...")

        # Stop server
        self.is_running = False

        # Close all active websocket connections
        if self.active_connections:
            logger.info(f"Closing {len(self.active_connections)} active connections...")
            close_tasks = []
            for websocket in list(self.active_connections):
                try:
                    # Notify client of shutdown
                    await websocket.send(json.dumps({
                        'status': 'shutdown',
                        'message': 'Server is shutting down'
                    }))
                    close_tasks.append(websocket.close())
                except Exception as e:
                    logger.debug(f"Error notifying client of shutdown: {e}")

            # Wait for all closes with timeout
            if close_tasks:
                try:
                    await asyncio.wait_for(asyncio.gather(*close_tasks, return_exceptions=True), timeout=5.0)
                except asyncio.TimeoutError:
                    logger.warning("Websocket close timeout, forcing shutdown")

        # Cleanup hardware resources
        self.cleanup()

        logger.success("✅ Graceful shutdown complete")


# =============================================================================
# MAIN
# =============================================================================

async def main():
    """Run GairiHead server with signal handling"""
    server = GairiHeadServer()

    # Shutdown event for signal handlers
    shutdown_event = asyncio.Event()

    def signal_handler(sig, frame):
        """Handle shutdown signals"""
        sig_name = signal.Signals(sig).name
        logger.info(f"📡 Received {sig_name} signal, initiating shutdown...")
        shutdown_event.set()

    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)  # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # systemd stop

    logger.info("Signal handlers registered (SIGINT, SIGTERM)")

    try:
        # Start server in background task
        server_task = asyncio.create_task(server.start())

        # Wait for shutdown signal
        await shutdown_event.wait()

        # Cancel server task
        server_task.cancel()

        # Graceful shutdown
        await server.shutdown_gracefully()

    except KeyboardInterrupt:
        logger.info("Server interrupted by user (KeyboardInterrupt)")
        await server.shutdown_gracefully()
    except Exception as e:
        logger.error(f"Server error: {e}")
        server.cleanup()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        # Already handled in main()
        pass
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
