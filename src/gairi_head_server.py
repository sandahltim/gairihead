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
from pathlib import Path
from typing import Optional, Dict, Any
import websockets
from loguru import logger
import yaml
import numpy as np
import cv2

# Audio recording
import sounddevice as sd
import soundfile as sf


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

        # Hardware managers (lazy init)
        self.camera_manager = None
        self.servo_controller = None
        self.arduino_display = None
        self.voice_handler = None
        self.expression_engine = None

        # Status
        self.is_running = False
        self.current_expression = "idle"

        logger.info(f"GairiHead server initialized on {host}:{port}")

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
                display_config = self.config.get('arduino_display', {})
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

    async def handle_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle incoming command from main Gary

        Args:
            command: Dict with 'action' and optional params

        Returns:
            Response dict with 'status', 'data', and optional 'error'
        """
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

            else:
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
                # Always release hardware lock
                coordinator.release()

        except Exception as e:
            logger.error(f"Failed to speak: {e}")
            return {
                'status': 'error',
                'error': f'Failed to speak: {e}'
            }

    async def handle_client(self, websocket):
        """Handle websocket client connection"""
        client_addr = websocket.remote_address
        logger.info(f"Client connected: {client_addr}")

        try:
            async for message in websocket:
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

    async def start(self):
        """Start websocket server"""
        logger.info(f"Starting GairiHead server on ws://{self.host}:{self.port}")

        self.is_running = True

        async with websockets.serve(self.handle_client, self.host, self.port):
            logger.success(f"✅ GairiHead server running on ws://{self.host}:{self.port}")
            await asyncio.Future()  # Run forever

    def cleanup(self):
        """Clean up resources"""
        if self.camera_manager:
            self.camera_manager.release()
        if self.servo_controller:
            self.servo_controller.cleanup()
        if self.arduino_display:
            self.arduino_display.close()
        logger.info("GairiHead server cleaned up")


# =============================================================================
# MAIN
# =============================================================================

async def main():
    """Run GairiHead server"""
    server = GairiHeadServer()

    try:
        await server.start()
    except KeyboardInterrupt:
        logger.info("Server interrupted by user")
    finally:
        server.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
