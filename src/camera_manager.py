"""
GairiHead Camera Manager
Unified interface for USB and Pi Camera Module with auto-detection

Supports:
- USB cameras (V4L2 via OpenCV)
- Pi Camera Module 3 (picamera2)
- Automatic fallback and detection
- Consistent numpy array output
"""

import cv2
import numpy as np
from loguru import logger
from pathlib import Path
import yaml
from typing import Optional, Tuple
import subprocess


class CameraManager:
    """Manages camera access with USB/CSI compatibility"""

    def __init__(self, config_path=None, prefer_picam=False):
        """
        Initialize camera with auto-detection

        Args:
            config_path: Path to gairi_head.yaml (defaults to ../config/gairi_head.yaml)
            prefer_picam: If True, try Pi Camera first, else try USB first
        """
        if config_path is None:
            # Default to config relative to this file
            config_path = Path(__file__).parent.parent / 'config' / 'gairi_head.yaml'

        self.config = self._load_config(config_path)
        self.camera_config = self.config['hardware']['pi5']
        self.camera = None
        self.camera_type = None
        self.is_opened = False

        # Get resolution and FPS from config
        self.width, self.height = self.camera_config['camera_resolution']
        self.fps = self.camera_config['camera_fps']

        # Try to initialize camera
        if prefer_picam:
            self._try_picamera() or self._try_usb_camera()
        else:
            self._try_usb_camera() or self._try_picamera()

        if not self.is_opened:
            raise RuntimeError("No camera found! Tried USB and Pi Camera Module.")

    def _load_config(self, config_path):
        """Load configuration file"""
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)

    def _try_usb_camera(self) -> bool:
        """Try to open USB camera via OpenCV"""
        try:
            logger.info("Attempting to open USB camera...")
            device_id = self.camera_config['camera_device']

            # Check if device exists
            video_device = f"/dev/video{device_id}"
            if not Path(video_device).exists():
                logger.warning(f"USB camera device {video_device} not found")
                return False

            self.camera = cv2.VideoCapture(device_id)

            if not self.camera.isOpened():
                logger.warning("USB camera found but failed to open")
                return False

            # Set resolution and FPS
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            self.camera.set(cv2.CAP_PROP_FPS, self.fps)

            # Test read
            ret, frame = self.camera.read()
            if not ret or frame is None:
                logger.warning("USB camera opened but failed to read frame")
                self.camera.release()
                return False

            self.camera_type = "USB"
            self.is_opened = True
            logger.success(f"✅ USB camera initialized: {self.width}x{self.height} @ {self.fps}fps")
            return True

        except Exception as e:
            logger.warning(f"USB camera initialization failed: {e}")
            return False

    def _try_picamera(self) -> bool:
        """Try to open Pi Camera Module via picamera2"""
        try:
            logger.info("Attempting to open Pi Camera Module...")

            # Check if picamera2 is available
            try:
                from picamera2 import Picamera2
            except ImportError:
                logger.warning("picamera2 not installed (install: sudo apt install python3-picamera2)")
                return False

            # Check if camera is detected
            result = subprocess.run(
                ['vcgencmd', 'get_camera'],
                capture_output=True,
                text=True,
                timeout=2
            )
            if 'detected=1' not in result.stdout:
                logger.warning("Pi Camera Module not detected by vcgencmd")
                return False

            self.camera = Picamera2()

            # Configure camera
            config = self.camera.create_preview_configuration(
                main={"size": (self.width, self.height), "format": "RGB888"}
            )
            self.camera.configure(config)
            self.camera.start()

            # Test capture
            frame = self.camera.capture_array()
            if frame is None or frame.size == 0:
                logger.warning("Pi Camera Module opened but failed to capture")
                self.camera.close()
                return False

            self.camera_type = "PiCamera"
            self.is_opened = True
            logger.success(f"✅ Pi Camera Module initialized: {self.width}x{self.height}")
            return True

        except Exception as e:
            logger.warning(f"Pi Camera Module initialization failed: {e}")
            return False

    def read_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        """
        Read a frame from camera

        Returns:
            (success: bool, frame: np.ndarray or None)
            Frame is always BGR format for OpenCV compatibility
        """
        if not self.is_opened:
            return False, None

        try:
            if self.camera_type == "USB":
                ret, frame = self.camera.read()
                return ret, frame

            elif self.camera_type == "PiCamera":
                # picamera2 returns RGB, convert to BGR for OpenCV
                frame = self.camera.capture_array()
                if frame is not None:
                    frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                    return True, frame_bgr
                return False, None

        except Exception as e:
            logger.error(f"Failed to read frame: {e}")
            return False, None

    def get_info(self) -> dict:
        """Get camera information"""
        return {
            "type": self.camera_type,
            "resolution": (self.width, self.height),
            "fps": self.fps,
            "is_opened": self.is_opened
        }

    def release(self):
        """Release camera resources"""
        if self.camera is not None:
            if self.camera_type == "USB":
                self.camera.release()
            elif self.camera_type == "PiCamera":
                self.camera.close()

            self.is_opened = False
            logger.info(f"{self.camera_type} camera released")

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.release()


# =============================================================================
# TESTING
# =============================================================================

def test_camera():
    """Test camera initialization and frame capture"""
    logger.info("Starting camera test...")

    try:
        with CameraManager() as cam:
            info = cam.get_info()
            logger.info(f"Camera info: {info}")

            # Capture and display 30 frames
            logger.info("Capturing 30 frames (press 'q' to quit early)...")
            for i in range(30):
                ret, frame = cam.read_frame()

                if not ret:
                    logger.error(f"Failed to read frame {i+1}")
                    break

                # Add frame counter
                cv2.putText(
                    frame,
                    f"Frame {i+1}/30 - {info['type']}",
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 255, 0),
                    2
                )

                # Display
                cv2.imshow('GairiHead Camera Test', frame)

                # Check for quit (1ms wait for key press)
                if cv2.waitKey(33) & 0xFF == ord('q'):  # ~30fps
                    logger.info("Test interrupted by user")
                    break

                if (i + 1) % 10 == 0:
                    logger.info(f"Captured {i+1} frames...")

            cv2.destroyAllWindows()
            logger.success("✅ Camera test complete!")

    except Exception as e:
        logger.error(f"Camera test failed: {e}")
        raise


def test_face_detection():
    """Test camera with basic face detection"""
    logger.info("Starting face detection test...")

    # Load Haar cascade
    cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    face_cascade = cv2.CascadeClassifier(cascade_path)

    if face_cascade.empty():
        logger.error("Failed to load face cascade!")
        return

    try:
        with CameraManager() as cam:
            info = cam.get_info()
            logger.info(f"Camera: {info['type']}")
            logger.info("Look at the camera! Press 'q' to quit...")

            frame_count = 0
            while True:
                ret, frame = cam.read_frame()

                if not ret:
                    logger.error("Failed to read frame")
                    break

                # Detect faces
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(30, 30))

                # Draw rectangles
                for (x, y, w, h) in faces:
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                    cv2.putText(
                        frame,
                        "Face detected!",
                        (x, y-10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (0, 255, 0),
                        2
                    )

                # Add info
                cv2.putText(
                    frame,
                    f"{info['type']} - Faces: {len(faces)}",
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 255, 0) if len(faces) > 0 else (0, 0, 255),
                    2
                )

                cv2.imshow('GairiHead Face Detection', frame)

                if cv2.waitKey(33) & 0xFF == ord('q'):
                    break

                frame_count += 1
                if frame_count % 30 == 0:
                    logger.info(f"Processed {frame_count} frames, {len(faces)} faces detected")

            cv2.destroyAllWindows()
            logger.success(f"✅ Face detection test complete! ({frame_count} frames)")

    except Exception as e:
        logger.error(f"Face detection test failed: {e}")
        raise


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "faces":
        test_face_detection()
    else:
        test_camera()
