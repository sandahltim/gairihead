"""
GairiHead Websocket Server
Allows main Gary agent to request camera snapshots, audio, and vision analysis

Commands from main Gary:
- capture_snapshot: Return base64 encoded camera frame
- record_audio: Record N seconds of audio, return base64 WAV
- analyze_scene: Capture frame + describe what's happening
- get_status: Return GairiHead status (camera, mic, expression)
- set_expression: Change facial expression
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
            from servo_controller import ServoController
            self.servo_controller = ServoController()
            logger.info("Servo controller initialized")
        return self.servo_controller

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

        # Test camera availability (without full init)
        camera_available = False
        try:
            import cv2
            test_cap = cv2.VideoCapture(0)
            if test_cap.isOpened():
                ret, _ = test_cap.read()
                camera_available = ret
            test_cap.release()
        except Exception as e:
            logger.warning(f"Camera test failed: {e}")
        
        # Test microphone availability
        microphone_available = False
        try:
            import sounddevice as sd
            # Quick test: try to query devices
            devices = sd.query_devices()
            # Check if there's at least one input device
            default_input = sd.query_devices(kind="input")
                if isinstance(dev, dict) and dev.get('max_input_channels', 0) > 0:
                    microphone_available = True
        except Exception as e:
            logger.warning(f"Microphone test failed: {e}")
        
        # Test servo availability (GPIO check)
        servos_available = False
        try:
            import RPi.GPIO as GPIO
            servos_available = True  # If import works, GPIO available
        except Exception:
            pass

        status = {
            'expression': self.current_expression,
            'camera_available': camera_available,
            'microphone_available': microphone_available,
            'servos_available': servos_available,
            'uptime': time.time(),
            'timestamp': time.time()
        }

        # If camera is initialized, get info
        if self.camera_manager:
            cam_info = self.camera_manager.get_info()
            status['camera'] = cam_info

        return {
            'status': 'success',
            'data': status
        }
    async def _handle_set_expression(self, params: Dict) -> Dict:
        """Set facial expression"""
        expression = params.get('expression', 'idle')
        logger.info(f"Setting expression: {expression}")

        try:
            servos = self._get_servos()
            servos.set_expression(expression)
            self.current_expression = expression

            return {
                'status': 'success',
                'data': {
                    'expression': expression,
                    'timestamp': time.time()
                }
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': f'Failed to set expression: {e}'
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
