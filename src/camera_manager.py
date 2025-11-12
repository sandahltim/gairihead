"""
GairiHead Camera Manager
Unified interface for USB and Pi Camera Module with auto-detection

Supports:
- Pi Camera Module 3 (picamera2) - DEFAULT
- USB cameras (V4L2 via OpenCV) - FALLBACK
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

    def __init__(self, config_path=None, prefer_picam=True, lazy_init=False):
        """
        Initialize camera with auto-detection

        Args:
            config_path: Path to gairi_head.yaml (defaults to ../config/gairi_head.yaml)
            prefer_picam: If True, try Pi Camera first, else try USB first (default: True)
            lazy_init: If True, don't open camera until first use (saves power, allows sharing)
        """
        if config_path is None:
            # Default to config relative to this file
            config_path = Path(__file__).parent.parent / 'config' / 'gairi_head.yaml'

        self.config = self._load_config(config_path)
        self.camera_config = self.config['hardware']['pi5']
        self.camera = None
        self.camera_type = None
        self.is_opened = False
        self.prefer_picam = prefer_picam
        self.lazy_init = lazy_init

        # Get resolution and FPS from config
        self.width, self.height = self.camera_config['camera_resolution']
        self.fps = self.camera_config['camera_fps']

        # Initialize immediately unless lazy init is enabled
        if not lazy_init:
            self._open_camera()

    def _open_camera(self):
        """Open camera device"""
        if self.is_opened:
            return True

        # Try to initialize camera
        if self.prefer_picam:
            success = self._try_picamera() or self._try_usb_camera()
        else:
            success = self._try_usb_camera() or self._try_picamera()

        if not success:
            raise RuntimeError("No camera found! Tried USB and Pi Camera Module.")

        return success

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

            # Check if picamera2 is available (import with system numpy compatibility)
            try:
                import sys
                # Temporarily prioritize system packages for picamera2 and dependencies
                original_path = sys.path.copy()
                sys.path = [p for p in sys.path if 'venv' not in p or 'site-packages' not in p]

                from picamera2 import Picamera2

                # Restore path but keep picamera2 loaded
                sys.path = original_path
            except ImportError as e:
                logger.warning(f"picamera2 not available: {e}")
                return False

            # Check if Pi Camera is detected (using picamera2, not vcgencmd which doesn't work on Pi 5)
            try:
                cameras = Picamera2.global_camera_info()
                # Look for Pi Camera (not USB webcam)
                picam_found = any('imx' in str(cam).lower() or 'ov' in str(cam).lower() for cam in cameras)
                if not picam_found:
                    logger.warning("Pi Camera Module not detected by picamera2")
                    return False
                logger.debug(f"Found Pi Camera in {len(cameras)} total cameras")
            except Exception as e:
                logger.warning(f"Failed to query cameras: {e}")
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
        # Lazy initialization - open camera on first use
        if not self.is_opened:
            try:
                self._open_camera()
            except Exception as e:
                logger.error(f"Failed to open camera: {e}")
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

    def close(self):
        """Close camera to free resources and allow other processes to use it"""
        if not self.is_opened:
            return

        try:
            if self.camera_type == "USB":
                self.camera.release()
            elif self.camera_type == "PiCamera":
                self.camera.close()

            self.is_opened = False
            self.camera = None
            logger.debug(f"{self.camera_type} camera closed")
        except Exception as e:
            logger.warning(f"Error closing camera: {e}")

    def is_available(self) -> bool:
        """Check if camera device exists (without locking it)"""
        # Check for USB camera
        for i in range(3):  # Check /dev/video0-2
            if Path(f"/dev/video{i}").exists():
                return True

        # Check for Pi Camera (using picamera2, not vcgencmd)
        try:
            import sys
            original_path = sys.path.copy()
            sys.path = [p for p in sys.path if 'venv' not in p or 'site-packages' not in p]

            from picamera2 import Picamera2

            sys.path = original_path

            cameras = Picamera2.global_camera_info()
            picam_found = any('imx' in str(cam).lower() or 'ov' in str(cam).lower() for cam in cameras)
            if picam_found:
                return True
        except:
            pass

        return False

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
