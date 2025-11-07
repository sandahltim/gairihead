#!/usr/bin/env python3
"""
Face Recognition Manager for GairiHead
Implements 3-tier authorization based on face recognition

Authorization Levels:
- Level 1: Main users (Tim + authorized) - Full Gary access
- Level 2: Guest mode (temporary auth) - Limited tools
- Level 3: Stranger mode (unknown) - Local LLM only

Version: 1.0
Date: 2025-11-07
"""

import face_recognition
import cv2
import numpy as np
import json
import os
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from loguru import logger
from datetime import datetime, timedelta


class FaceRecognitionManager:
    """Manages face recognition and authorization for GairiHead"""

    def __init__(self, config_path: str = "/home/tim/gairihead/config"):
        """
        Initialize face recognition manager

        Args:
            config_path: Path to configuration directory
        """
        self.config_path = Path(config_path)
        self.data_path = Path("/home/tim/gairihead/data")
        self.authorized_faces_dir = self.data_path / "authorized_faces"
        self.stranger_logs_dir = self.data_path / "stranger_logs"
        self.guest_tokens_file = self.data_path / "guest_tokens.json"

        # Create directories
        self.authorized_faces_dir.mkdir(parents=True, exist_ok=True)
        self.stranger_logs_dir.mkdir(parents=True, exist_ok=True)

        # Load authorized face encodings
        self.authorized_users = {}  # {user_name: {'encodings': [], 'level': int}}
        self._load_authorized_faces()

        # Guest tokens (temporary authorization)
        self.guest_tokens = {}  # {token: {'expires': datetime, 'level': 2}}
        self._load_guest_tokens()

        # Recognition settings
        self.tolerance = 0.6  # Lower = stricter matching
        self.min_confidence = 0.7  # Minimum confidence to recognize

        logger.info(f"Face recognition initialized: {len(self.authorized_users)} authorized users")

    def _load_authorized_faces(self):
        """Load authorized face encodings from disk"""
        if not self.authorized_faces_dir.exists():
            logger.warning("No authorized faces directory found")
            return

        for user_dir in self.authorized_faces_dir.iterdir():
            if not user_dir.is_dir():
                continue

            user_name = user_dir.name
            encodings = []

            # Load metadata (authorization level)
            metadata_file = user_dir / "metadata.json"
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                    level = metadata.get('level', 1)
            else:
                level = 1  # Default: main user

            # Load face encodings from images
            for img_file in user_dir.glob("*.jpg"):
                try:
                    image = face_recognition.load_image_file(str(img_file))
                    face_encodings = face_recognition.face_encodings(image)

                    if face_encodings:
                        encodings.append(face_encodings[0])
                        logger.debug(f"Loaded encoding from {img_file.name}")
                    else:
                        logger.warning(f"No face found in {img_file.name}")

                except Exception as e:
                    logger.error(f"Error loading {img_file}: {e}")

            if encodings:
                self.authorized_users[user_name] = {
                    'encodings': encodings,
                    'level': level
                }
                logger.info(f"Loaded {len(encodings)} encodings for {user_name} (level {level})")
            else:
                logger.warning(f"No valid encodings for {user_name}")

    def _load_guest_tokens(self):
        """Load guest tokens from disk"""
        if self.guest_tokens_file.exists():
            try:
                with open(self.guest_tokens_file, 'r') as f:
                    data = json.load(f)
                    # Convert ISO strings to datetime
                    self.guest_tokens = {
                        token: {
                            'expires': datetime.fromisoformat(info['expires']),
                            'level': info.get('level', 2)
                        }
                        for token, info in data.items()
                    }
                logger.info(f"Loaded {len(self.guest_tokens)} guest tokens")
            except Exception as e:
                logger.error(f"Error loading guest tokens: {e}")
                self.guest_tokens = {}

    def _save_guest_tokens(self):
        """Save guest tokens to disk"""
        try:
            # Convert datetime to ISO strings
            data = {
                token: {
                    'expires': info['expires'].isoformat(),
                    'level': info['level']
                }
                for token, info in self.guest_tokens.items()
            }

            with open(self.guest_tokens_file, 'w') as f:
                json.dump(data, f, indent=2)

            logger.debug("Guest tokens saved")
        except Exception as e:
            logger.error(f"Error saving guest tokens: {e}")

    def recognize_face(self, image_array: np.ndarray) -> Dict:
        """
        Recognize face in image and determine authorization level

        Args:
            image_array: Image as numpy array (BGR from OpenCV or RGB)

        Returns:
            dict: {
                'user': str (user name or 'unknown'),
                'level': int (1=main, 2=guest, 3=stranger),
                'confidence': float (0.0-1.0),
                'face_location': tuple or None
            }
        """
        # Convert BGR to RGB if needed (OpenCV uses BGR)
        if len(image_array.shape) == 3 and image_array.shape[2] == 3:
            # Assume BGR from OpenCV, convert to RGB
            rgb_image = cv2.cvtColor(image_array, cv2.COLOR_BGR2RGB)
        else:
            rgb_image = image_array

        # Detect faces
        face_locations = face_recognition.face_locations(rgb_image)

        if not face_locations:
            logger.debug("No faces detected in image")
            return {
                'user': 'none',
                'level': 3,  # Default to stranger mode if no face
                'confidence': 0.0,
                'face_location': None
            }

        # Use first face (largest)
        face_location = face_locations[0]

        # Get face encoding
        face_encodings = face_recognition.face_encodings(rgb_image, [face_location])

        if not face_encodings:
            logger.warning("Face detected but encoding failed")
            return {
                'user': 'unknown',
                'level': 3,
                'confidence': 0.0,
                'face_location': face_location
            }

        face_encoding = face_encodings[0]

        # Compare with authorized users
        best_match = None
        best_distance = float('inf')

        for user_name, user_data in self.authorized_users.items():
            encodings = user_data['encodings']

            # Compare face with all known encodings for this user
            distances = face_recognition.face_distance(encodings, face_encoding)
            min_distance = min(distances) if distances.size > 0 else float('inf')

            if min_distance < best_distance:
                best_distance = min_distance
                best_match = user_name

        # Determine if match is confident enough
        if best_match and best_distance < self.tolerance:
            confidence = 1.0 - best_distance
            level = self.authorized_users[best_match]['level']

            logger.info(f"✅ Recognized {best_match} (level {level}, confidence: {confidence:.2f})")

            return {
                'user': best_match,
                'level': level,
                'confidence': confidence,
                'face_location': face_location
            }
        else:
            # Unknown face (stranger)
            logger.warning(f"⚠️  Unknown face detected (distance: {best_distance:.2f})")

            # Log stranger
            self._log_stranger(rgb_image, face_location)

            return {
                'user': 'unknown',
                'level': 3,
                'confidence': 0.0,
                'face_location': face_location
            }

    def _log_stranger(self, image: np.ndarray, face_location: tuple):
        """
        Log stranger interaction with photo

        Args:
            image: Image array (RGB)
            face_location: Face bounding box
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"stranger_{timestamp}.jpg"
            filepath = self.stranger_logs_dir / filename

            # Draw box around face
            top, right, bottom, left = face_location
            cv2.rectangle(image, (left, top), (right, bottom), (0, 255, 0), 2)

            # Convert RGB to BGR for OpenCV
            bgr_image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

            # Save image
            cv2.imwrite(str(filepath), bgr_image)

            logger.warning(f"📸 Stranger photo saved: {filename}")

            # Save metadata
            metadata_file = filepath.with_suffix('.json')
            with open(metadata_file, 'w') as f:
                json.dump({
                    'timestamp': timestamp,
                    'face_location': face_location,
                    'type': 'stranger'
                }, f, indent=2)

        except Exception as e:
            logger.error(f"Error logging stranger: {e}")

    def create_guest_token(self, duration_hours: int = 1) -> str:
        """
        Create temporary guest authorization token

        Args:
            duration_hours: How long token is valid (hours)

        Returns:
            str: Guest token
        """
        import secrets

        token = secrets.token_urlsafe(16)
        expires = datetime.now() + timedelta(hours=duration_hours)

        self.guest_tokens[token] = {
            'expires': expires,
            'level': 2  # Guest mode
        }

        self._save_guest_tokens()

        logger.info(f"✅ Guest token created (expires in {duration_hours}h)")

        return token

    def check_guest_token(self, token: str) -> Optional[int]:
        """
        Check if guest token is valid

        Args:
            token: Guest token to check

        Returns:
            int or None: Authorization level if valid, None if expired/invalid
        """
        if token not in self.guest_tokens:
            return None

        token_data = self.guest_tokens[token]

        # Check if expired
        if datetime.now() > token_data['expires']:
            logger.info(f"Guest token expired, removing")
            del self.guest_tokens[token]
            self._save_guest_tokens()
            return None

        return token_data['level']

    def revoke_guest_token(self, token: str) -> bool:
        """
        Revoke guest token

        Args:
            token: Token to revoke

        Returns:
            bool: True if revoked, False if not found
        """
        if token in self.guest_tokens:
            del self.guest_tokens[token]
            self._save_guest_tokens()
            logger.info("Guest token revoked")
            return True
        return False

    def add_authorized_user(self, name: str, image_paths: List[str], level: int = 1):
        """
        Add new authorized user

        Args:
            name: User name
            image_paths: List of paths to training images
            level: Authorization level (1=main, 2=guest)
        """
        user_dir = self.authorized_faces_dir / name
        user_dir.mkdir(parents=True, exist_ok=True)

        # Save metadata
        metadata_file = user_dir / "metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump({
                'name': name,
                'level': level,
                'created': datetime.now().isoformat()
            }, f, indent=2)

        # Copy training images
        encodings = []
        for i, img_path in enumerate(image_paths):
            try:
                # Load and verify face
                image = face_recognition.load_image_file(img_path)
                face_encodings = face_recognition.face_encodings(image)

                if not face_encodings:
                    logger.warning(f"No face found in {img_path}")
                    continue

                encodings.append(face_encodings[0])

                # Copy image
                dest_path = user_dir / f"face_{i:02d}.jpg"
                import shutil
                shutil.copy(img_path, dest_path)

                logger.info(f"Added training image: {dest_path.name}")

            except Exception as e:
                logger.error(f"Error processing {img_path}: {e}")

        if encodings:
            self.authorized_users[name] = {
                'encodings': encodings,
                'level': level
            }
            logger.success(f"✅ Added {name} with {len(encodings)} face encodings (level {level})")
        else:
            logger.error(f"❌ No valid face encodings for {name}")


# =============================================================================
# Testing
# =============================================================================

def test_face_recognition():
    """Test face recognition with webcam"""
    manager = FaceRecognitionManager()

    # Open webcam
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        logger.error("Cannot open webcam")
        return

    logger.info("Press 'q' to quit")

    while True:
        ret, frame = cap.read()

        if not ret:
            logger.error("Failed to grab frame")
            break

        # Recognize face
        result = manager.recognize_face(frame)

        # Draw results
        if result['face_location']:
            top, right, bottom, left = result['face_location']

            # Color based on authorization level
            if result['level'] == 1:
                color = (0, 255, 0)  # Green - main user
                label = f"{result['user']} (AUTHORIZED)"
            elif result['level'] == 2:
                color = (255, 255, 0)  # Yellow - guest
                label = f"{result['user']} (GUEST)"
            else:
                color = (0, 0, 255)  # Red - stranger
                label = "STRANGER"

            # Draw box
            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)

            # Draw label
            cv2.rectangle(frame, (left, bottom - 25), (right, bottom), color, cv2.FILLED)
            cv2.putText(frame, label, (left + 6, bottom - 6),
                       cv2.FONT_HERSHEY_DUPLEX, 0.5, (255, 255, 255), 1)

        # Show frame
        cv2.imshow('GairiHead Face Recognition', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    test_face_recognition()
