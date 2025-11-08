#!/usr/bin/env python3
"""
Vision Handler - Camera, face detection, and tracking for GairiHead

Handles:
- Pi Camera Module 3 capture
- Face detection (OpenCV)
- Face recognition (known faces vs strangers)
- Eye tracking (servo positions to follow faces)
- Motion detection
"""

import cv2
import numpy as np
import time
import threading
from pathlib import Path
from loguru import logger

class VisionHandler:
    """Manages camera and computer vision features"""

    def __init__(self, config, expression_engine=None):
        """
        Initialize vision handler

        Args:
            config: Configuration dict from gairi_head.yaml
            expression_engine: ExpressionEngine instance for reactions
        """
        self.config = config.get('vision', {})
        self.hardware_config = config.get('hardware', {}).get('pi5', {})
        self.expression_engine = expression_engine

        # Camera setup
        self.camera_device = self.hardware_config.get('camera_device', 0)
        self.camera_resolution = tuple(self.hardware_config.get('camera_resolution', [640, 480]))
        self.camera_fps = self.hardware_config.get('camera_fps', 5)

        self.camera = None
        self.frame = None
        self.running = False

        # Face detection
        self.face_detection_enabled = self.config.get('face_detection', {}).get('enabled', True)
        self.cascade_path = self.config.get('face_detection', {}).get('cascade',
                                           'haarcascade_frontalface_default.xml')
        self.face_cascade = None

        # Face recognition
        self.face_recognition_enabled = self.config.get('face_recognition', {}).get('enabled', True)
        self.known_faces_dir = Path(self.config.get('face_recognition', {}).get('known_faces_dir',
                                                                                  '/Gary/GairiHead/data/faces'))
        self.known_faces = {}  # {name: encoding}
        self.tolerance = self.config.get('face_recognition', {}).get('tolerance', 0.6)

        # Tracking
        self.tracking_enabled = self.config.get('tracking', {}).get('enabled', True)
        self.smooth_factor = self.config.get('tracking', {}).get('smooth_factor', 0.3)
        self.current_target = None  # (x, y) normalized position
        self.last_face_time = 0

        # Motion detection
        self.motion_detection_enabled = self.config.get('face_detection', {}).get('enabled', True)
        self.previous_frame = None
        self.motion_threshold = 5000  # Pixel change threshold

        # Threading
        self.capture_thread = None
        self.frame_lock = threading.Lock()

        logger.info("VisionHandler initialized")

    def start(self):
        """Start camera and vision processing"""
        logger.info("Starting vision handler...")

        # Initialize camera
        try:
            self.camera = cv2.VideoCapture(self.camera_device)
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.camera_resolution[0])
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.camera_resolution[1])
            self.camera.set(cv2.CAP_PROP_FPS, self.camera_fps)

            if not self.camera.isOpened():
                raise Exception(f"Failed to open camera {self.camera_device}")

            logger.info(f"Camera opened: {self.camera_resolution[0]}x{self.camera_resolution[1]} @ {self.camera_fps}fps")
        except Exception as e:
            logger.error(f"Camera initialization failed: {e}")
            return False

        # Load face detection cascade
        if self.face_detection_enabled:
            try:
                # Try OpenCV data directory
                cascade_full_path = cv2.data.haarcascades + self.cascade_path
                self.face_cascade = cv2.CascadeClassifier(cascade_full_path)

                if self.face_cascade.empty():
                    raise Exception("Failed to load face cascade")

                logger.info("Face detection cascade loaded")
            except Exception as e:
                logger.warning(f"Face detection disabled: {e}")
                self.face_detection_enabled = False

        # Load known faces
        if self.face_recognition_enabled:
            self.load_known_faces()

        # Start capture thread
        self.running = True
        self.capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.capture_thread.start()

        logger.info("Vision handler started")
        return True

    def stop(self):
        """Stop camera and vision processing"""
        logger.info("Stopping vision handler...")
        self.running = False

        if self.capture_thread:
            self.capture_thread.join(timeout=2.0)

        if self.camera:
            self.camera.release()

        logger.info("Vision handler stopped")

    def _capture_loop(self):
        """Background thread for continuous frame capture"""
        while self.running:
            try:
                ret, frame = self.camera.read()

                if not ret:
                    logger.warning("Frame capture failed")
                    time.sleep(0.1)
                    continue

                with self.frame_lock:
                    self.frame = frame

                # Process frame
                self._process_frame(frame)

                # Limit frame rate
                time.sleep(1.0 / self.camera_fps)

            except Exception as e:
                logger.error(f"Capture loop error: {e}")
                time.sleep(1.0)

    def _process_frame(self, frame):
        """Process a single frame"""
        # Face detection
        if self.face_detection_enabled:
            faces = self.detect_faces(frame)

            if faces:
                self.last_face_time = time.time()

                # Track largest face
                largest_face = max(faces, key=lambda f: f[2] * f[3])
                self._track_face(largest_face, frame.shape)

                # Expression reaction
                if self.expression_engine:
                    # New face detected
                    if len(faces) > 0:
                        self.expression_engine.set_expression('alert')

        # Motion detection
        if self.motion_detection_enabled:
            motion_level = self.detect_motion(frame)

            if motion_level > self.motion_threshold:
                logger.debug(f"Motion detected: {motion_level}")

    def detect_faces(self, frame):
        """
        Detect faces in frame

        Args:
            frame: OpenCV frame (BGR)

        Returns:
            list: List of face rectangles [(x, y, w, h), ...]
        """
        if not self.face_detection_enabled:
            return []

        # Lazy-load face cascade if not already loaded
        if self.face_cascade is None:
            try:
                cascade_full_path = cv2.data.haarcascades + self.cascade_path
                self.face_cascade = cv2.CascadeClassifier(cascade_full_path)

                if self.face_cascade.empty():
                    logger.error("Failed to load face cascade")
                    return []

                logger.debug("Face detection cascade lazy-loaded")
            except Exception as e:
                logger.error(f"Failed to load cascade: {e}")
                return []

        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Detect faces
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=self.config.get('face_detection', {}).get('scale_factor', 1.1),
            minNeighbors=self.config.get('face_detection', {}).get('min_neighbors', 5),
            minSize=tuple(self.config.get('face_detection', {}).get('min_size', [30, 30]))
        )

        return faces.tolist() if len(faces) > 0 else []

    def _track_face(self, face_rect, frame_shape):
        """
        Track face position and update servo targets

        Args:
            face_rect: (x, y, w, h) of face
            frame_shape: (height, width, channels) of frame
        """
        if not self.tracking_enabled:
            return

        x, y, w, h = face_rect
        frame_h, frame_w = frame_shape[:2]

        # Calculate face center
        face_center_x = (x + w/2) / frame_w  # 0.0 to 1.0
        face_center_y = (y + h/2) / frame_h  # 0.0 to 1.0

        # Normalize to -1.0 to 1.0 (center is 0)
        normalized_x = (face_center_x - 0.5) * 2.0
        normalized_y = (face_center_y - 0.5) * 2.0

        # Smooth tracking
        if self.current_target:
            smoothed_x = self.current_target[0] + (normalized_x - self.current_target[0]) * self.smooth_factor
            smoothed_y = self.current_target[1] + (normalized_y - self.current_target[1]) * self.smooth_factor
            self.current_target = (smoothed_x, smoothed_y)
        else:
            self.current_target = (normalized_x, normalized_y)

        # Update expression engine
        if self.expression_engine:
            self.expression_engine.look_at(self.current_target[0], self.current_target[1])

    def detect_motion(self, frame):
        """
        Detect motion between frames

        Args:
            frame: Current frame

        Returns:
            int: Motion level (pixel difference count)
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)

        if self.previous_frame is None:
            self.previous_frame = gray
            return 0

        # Calculate difference
        frame_delta = cv2.absdiff(self.previous_frame, gray)
        thresh = cv2.threshold(frame_delta, 25, 255, cv2.THRESH_BINARY)[1]

        # Count changed pixels
        motion_level = np.sum(thresh) / 255

        self.previous_frame = gray

        return motion_level

    def load_known_faces(self):
        """Load known face encodings from disk"""
        logger.info(f"Loading known faces from {self.known_faces_dir}")

        if not self.known_faces_dir.exists():
            self.known_faces_dir.mkdir(parents=True, exist_ok=True)
            logger.info("Created known faces directory")
            return

        try:
            import face_recognition
            import os

            # Load all images from subdirectories (e.g., known_faces/tim/*.jpg)
            for person_dir in self.known_faces_dir.iterdir():
                if not person_dir.is_dir():
                    continue

                person_name = person_dir.name.title()
                logger.debug(f"Loading faces for: {person_name}")

                # Collect all encodings for this person
                encodings = []

                for image_file in person_dir.glob('*.jpg'):
                    try:
                        # Load image and extract face encoding
                        image = face_recognition.load_image_file(str(image_file))
                        file_encodings = face_recognition.face_encodings(image)

                        if len(file_encodings) > 0:
                            encodings.append(file_encodings[0])
                            logger.debug(f"  Loaded: {image_file.name}")
                        else:
                            logger.warning(f"  No face in: {image_file.name}")
                    except Exception as e:
                        logger.warning(f"  Failed to load {image_file.name}: {e}")

                # Average all encodings for this person (more robust recognition)
                if len(encodings) > 0:
                    import numpy as np
                    avg_encoding = np.mean(encodings, axis=0)
                    self.known_faces[person_name] = avg_encoding
                    logger.info(f"Loaded {len(encodings)} face encodings for: {person_name}")

            logger.info(f"Loaded {len(self.known_faces)} known people")

        except ImportError:
            logger.warning("face_recognition library not installed - face recognition disabled")
            logger.info("Install with: pip install face_recognition")
            self.face_recognition_enabled = False
        except Exception as e:
            logger.error(f"Error loading known faces: {e}")
            self.face_recognition_enabled = False

    def recognize_face(self, frame, face_rect):
        """
        Recognize a detected face

        Args:
            frame: OpenCV frame
            face_rect: (x, y, w, h) of face

        Returns:
            str: Name of recognized person or "Unknown"
        """
        if not self.face_recognition_enabled:
            return "Unknown"

        # Lazy-load known faces if not already loaded
        if len(self.known_faces) == 0:
            self.load_known_faces()
            if len(self.known_faces) == 0:
                return "Unknown"

        try:
            import face_recognition

            x, y, w, h = face_rect

            # Extract face region (convert to RGB for face_recognition library)
            face_image = frame[y:y+h, x:x+w]
            rgb_face = cv2.cvtColor(face_image, cv2.COLOR_BGR2RGB)

            # Get face encoding
            encodings = face_recognition.face_encodings(rgb_face)

            if len(encodings) == 0:
                return "Unknown"

            face_encoding = encodings[0]

            # Compare with known faces
            for name, known_encoding in self.known_faces.items():
                # Calculate distance (lower = more similar)
                distance = face_recognition.face_distance([known_encoding], face_encoding)[0]

                if distance < self.tolerance:
                    logger.debug(f"Recognized {name} (distance: {distance:.2f})")
                    return name

            return "Unknown"

        except Exception as e:
            logger.error(f"Face recognition error: {e}")
            return "Unknown"

    def get_frame(self):
        """
        Get current frame (thread-safe)

        Returns:
            numpy.ndarray: Current frame or None
        """
        with self.frame_lock:
            return self.frame.copy() if self.frame is not None else None

    def get_status(self):
        """
        Get vision status

        Returns:
            dict: Status information
        """
        return {
            'camera_active': self.camera is not None and self.camera.isOpened(),
            'face_detection': self.face_detection_enabled,
            'face_recognition': self.face_recognition_enabled,
            'tracking': self.tracking_enabled,
            'current_target': self.current_target,
            'time_since_face': time.time() - self.last_face_time if self.last_face_time > 0 else None
        }


# Example usage and testing
if __name__ == '__main__':
    import yaml
    from loguru import logger
    import sys

    # Configure logging
    logger.remove()
    logger.add(sys.stderr, level="DEBUG")

    print("VisionHandler Test")
    print("=" * 60)

    # Load config
    with open('/home/tim/GairiHead/config/gairi_head.yaml', 'r') as f:
        config = yaml.safe_load(f)

    # Initialize handler
    handler = VisionHandler(config)

    # Start vision
    if handler.start():
        print("\n✅ Vision handler started")
        print("\nRunning for 10 seconds...")

        try:
            for i in range(10):
                time.sleep(1)
                status = handler.get_status()
                print(f"  [{i+1}/10] Status: {status}")

        except KeyboardInterrupt:
            print("\nInterrupted by user")

        finally:
            handler.stop()
            print("\n✅ Vision handler test complete")
    else:
        print("\n❌ Vision handler failed to start")
        print("Note: This is expected if no camera is connected yet")
