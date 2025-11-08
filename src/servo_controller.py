"""
GairiHead Servo Controller
Controls eyelids and mouth servos on Pi 5

Hardware (M.2 HAT safe pins):
- Left eyelid: GPIO 17 (Pin 11)
- Right eyelid: GPIO 27 (Pin 13)
- Mouth: GPIO 22 (Pin 15)

v2.0 - Enhanced with smooth interpolation, micro-expressions, TARS personality
"""

import time
import math
import random
import threading
from gpiozero import Servo, Device
from gpiozero.pins.lgpio import LGPIOFactory
from loguru import logger
import yaml
from pathlib import Path


class ServoController:
    """Manages servo positions for eyelids and mouth"""

    def __init__(self, config_path="/Gary/GairiHead/config/gairi_head.yaml"):
        """Initialize servos with config"""
        self.config = self._load_config(config_path)

        # Use lgpio for Pi 5 (native GPIO library)
        try:
            Device.pin_factory = LGPIOFactory()
            factory = Device.pin_factory
            logger.info("Using lgpio pin factory (Pi 5 native)")
        except Exception as e:
            logger.warning(f"lgpio not available, using default: {e}")
            factory = None

        # Initialize servos
        servo_config = self.config['hardware']['servos']

        self.left_eyelid = Servo(
            servo_config['left_eyelid']['gpio_pin'],
            min_pulse_width=0.5/1000,
            max_pulse_width=2.5/1000,
            pin_factory=factory
        )

        self.right_eyelid = Servo(
            servo_config['right_eyelid']['gpio_pin'],
            min_pulse_width=0.5/1000,
            max_pulse_width=2.5/1000,
            pin_factory=factory
        )

        self.mouth = Servo(
            servo_config['mouth']['gpio_pin'],
            min_pulse_width=0.5/1000,
            max_pulse_width=2.5/1000,
            pin_factory=factory
        )

        # Store angle ranges
        self.left_config = servo_config['left_eyelid']
        self.right_config = servo_config['right_eyelid']
        self.mouth_config = servo_config['mouth']

        # Track current positions for smooth transitions
        self.current_left = self.left_config['neutral_angle']
        self.current_right = self.right_config['neutral_angle']
        self.current_mouth = self.mouth_config['neutral_angle']

        # Movement lock for thread safety
        self.movement_lock = threading.Lock()

        # Personality settings
        self.blink_variation = 0.3  # 30% timing variation for natural blinks
        self.lazy_eye_enabled = False  # Slight lag between eyes for character
        self.lazy_eye_delay = 0.05  # seconds

        # Speech animation
        self.speech_animation_active = False
        self._speech_animation_thread = None

        # Set to neutral
        self.reset_to_neutral()

        logger.info("Servo controller initialized (v2.0 - smooth movement)")

    def _load_config(self, config_path):
        """Load configuration file"""
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)

    def reset_to_neutral(self):
        """Reset all servos to neutral position"""
        self.set_left_eyelid(self.left_config['neutral_angle'])
        self.set_right_eyelid(self.right_config['neutral_angle'])
        self.set_mouth(self.mouth_config['neutral_angle'])
        logger.info("Servos reset to neutral")

    def angle_to_servo_value(self, angle, min_angle, max_angle):
        """
        Convert angle (0-90) to servo value (-1 to 1)

        Servo.value expects -1 (min) to 1 (max)
        We map our angle range to this
        """
        # Normalize angle to 0-1 range
        normalized = (angle - min_angle) / (max_angle - min_angle)
        # Convert to -1 to 1 range
        return (normalized * 2) - 1

    def angle_to_servo_value_left_eye(self, angle):
        """
        CALIBRATED mapping for left eyelid (MG90S servo on GPIO 17)

        Physical calibration data from precise_servo_calibration.py:
        - 0° (fully closed) → servo 0.100
        - 75° (fully open)  → servo -0.310
        - Working range: 0.410 span

        Note: Using 75° as max instead of 90° due to mechanism physical limit
        """
        # Clamp to physical range
        angle = max(0, min(75, angle))

        # Normalize to 0-1 (0° = 0, 75° = 1)
        normalized = angle / 75.0

        # Map to calibrated servo range: 0.100 to -0.310
        servo_value = 0.100 - (normalized * 0.410)

        return servo_value

    def angle_to_servo_value_right_eye(self, angle):
        """
        CALIBRATED mapping for right eyelid (MG90S servo on GPIO 27)

        Uses INVERTED left eye calibration for symmetric movement
        - Left eye: 0.100 (closed) to -0.310 (open)
        - Right eye: -0.100 (closed) to 0.310 (open) [MIRRORED]
        - Working range: 0.410 span (SAME as left eye)

        Note: Right eye servo is mechanically identical but mounted opposite
        """
        # Clamp to physical range
        angle = max(0, min(75, angle))

        # Normalize to 0-1 (0° = 0, 75° = 1)
        normalized = angle / 75.0

        # Inverted left eye formula: -(0.100 - (normalized * 0.410))
        servo_value = -0.100 + (normalized * 0.410)

        return servo_value

    def angle_to_servo_value_mouth(self, angle):
        """
        CALIBRATED mapping for mouth (MG90S servo on GPIO 22)

        Physical calibration data from precise_servo_calibration.py:
        - 0° (fully closed) → servo 0.000
        - 60° (fully open)  → servo -0.600
        - Working range: 0.600 span

        Note: Mouth uses 0-60° range (smaller than eyes' 0-75°)
        """
        # Clamp to physical range
        angle = max(0, min(60, angle))

        # Normalize to 0-1 (0° = 0, 60° = 1)
        normalized = angle / 60.0

        # Map to calibrated servo range: 0.000 to -0.600
        servo_value = 0.000 - (normalized * 0.600)

        return servo_value

    # =========================================================================
    # SMOOTH MOVEMENT & EASING
    # =========================================================================

    @staticmethod
    def ease_in_out_cubic(t):
        """
        Cubic easing function for smooth, natural movement

        Args:
            t: Progress from 0 to 1

        Returns:
            Eased value (0 to 1)
        """
        if t < 0.5:
            return 4 * t * t * t
        else:
            p = 2 * t - 2
            return 1 + p * p * p / 2

    @staticmethod
    def ease_out_bounce(t):
        """
        Bounce easing for playful expressions

        Args:
            t: Progress from 0 to 1

        Returns:
            Eased value with bounce (0 to 1)
        """
        if t < 1 / 2.75:
            return 7.5625 * t * t
        elif t < 2 / 2.75:
            t -= 1.5 / 2.75
            return 7.5625 * t * t + 0.75
        elif t < 2.5 / 2.75:
            t -= 2.25 / 2.75
            return 7.5625 * t * t + 0.9375
        else:
            t -= 2.625 / 2.75
            return 7.5625 * t * t + 0.984375

    def _smooth_transition(self, servo, target_angle, current_angle,
                          duration=0.3, steps=15, easing='cubic'):
        """
        Smoothly transition servo from current to target angle

        Args:
            servo: Servo object to move
            target_angle: Target angle
            current_angle: Current angle
            duration: Transition duration in seconds
            steps: Number of interpolation steps
            easing: 'cubic', 'bounce', or 'linear'

        Returns:
            Final angle reached
        """
        if abs(target_angle - current_angle) < 1:  # Already there
            return target_angle

        step_delay = duration / steps

        for i in range(steps + 1):
            # Calculate progress (0 to 1)
            progress = i / steps

            # Apply easing
            if easing == 'cubic':
                eased_progress = self.ease_in_out_cubic(progress)
            elif easing == 'bounce':
                eased_progress = self.ease_out_bounce(progress)
            else:  # linear
                eased_progress = progress

            # Interpolate angle
            angle = current_angle + (target_angle - current_angle) * eased_progress

            # Apply to servo
            servo.value = angle

            time.sleep(step_delay)

        return target_angle

    def set_left_eyelid(self, angle, smooth=True, duration=0.25):
        """
        Set left eyelid angle (0=closed, 75=wide open)

        CALIBRATED for MG90S servo on GPIO 17
        Uses precise calibration data from physical testing

        Args:
            angle: Target angle (0-75°)
            smooth: Use smooth interpolation
            duration: Transition duration if smooth
        """
        # Clamp to calibrated physical range (0-75°)
        angle = max(0, min(75, angle))

        with self.movement_lock:
            if smooth:
                # Use CALIBRATED mapping
                current_value = self.angle_to_servo_value_left_eye(self.current_left)
                target_value = self.angle_to_servo_value_left_eye(angle)

                # Smooth transition
                self._smooth_transition(self.left_eyelid, target_value,
                                       current_value, duration)
            else:
                # Instant - use CALIBRATED mapping
                value = self.angle_to_servo_value_left_eye(angle)
                self.left_eyelid.value = value

            self.current_left = angle

    def set_right_eyelid(self, angle, smooth=True, duration=0.25):
        """
        Set right eyelid angle (0=closed, 75=wide open)

        CALIBRATED for MG90S servo on GPIO 27
        Uses precise calibration data from physical testing

        Args:
            angle: Target angle (0-75°)
            smooth: Use smooth interpolation
            duration: Transition duration if smooth
        """
        # Clamp to calibrated physical range (0-75°)
        angle = max(0, min(75, angle))

        # Lazy eye delay if enabled
        if self.lazy_eye_enabled and smooth:
            time.sleep(self.lazy_eye_delay)

        with self.movement_lock:
            if smooth:
                # Use CALIBRATED mapping
                current_value = self.angle_to_servo_value_right_eye(self.current_right)
                target_value = self.angle_to_servo_value_right_eye(angle)

                # Smooth transition
                self._smooth_transition(self.right_eyelid, target_value,
                                       current_value, duration)
            else:
                # Instant - use CALIBRATED mapping
                value = self.angle_to_servo_value_right_eye(angle)
                self.right_eyelid.value = value

            self.current_right = angle

    def set_mouth(self, angle, smooth=True, duration=0.2):
        """
        Set mouth angle (0=closed, 60=wide open)

        CALIBRATED for MG90S servo on GPIO 22
        Uses precise calibration data from physical testing

        Args:
            angle: Target angle (0-60°)
            smooth: Use smooth interpolation
            duration: Transition duration if smooth
        """
        # Clamp to calibrated physical range (0-60°)
        angle = max(0, min(60, angle))

        with self.movement_lock:
            if smooth:
                # Use CALIBRATED mapping
                current_value = self.angle_to_servo_value_mouth(self.current_mouth)
                target_value = self.angle_to_servo_value_mouth(angle)

                # Smooth transition
                self._smooth_transition(self.mouth, target_value,
                                       current_value, duration)
            else:
                # Instant - use CALIBRATED mapping
                value = self.angle_to_servo_value_mouth(angle)
                self.mouth.value = value

            self.current_mouth = angle

    # =========================================================================
    # PERSONALITY METHODS - TARS Character
    # =========================================================================

    def blink(self, duration=None, natural_variation=True):
        """
        Perform a blink with natural variation

        Args:
            duration: Blink duration (None for auto with variation)
            natural_variation: Add timing variation for realism
        """
        # Add natural variation to blink speed
        if duration is None:
            base_duration = 0.12
            if natural_variation:
                duration = base_duration * (1 + random.uniform(-self.blink_variation,
                                                               self.blink_variation))
            else:
                duration = base_duration

        # Store current positions
        left_current = self.current_left
        right_current = self.current_right

        # Close (fast)
        self.set_left_eyelid(0, smooth=True, duration=duration * 0.4)
        self.set_right_eyelid(0, smooth=True, duration=duration * 0.4)

        # Brief pause
        time.sleep(duration * 0.2)

        # Open (slightly slower for natural look)
        self.set_left_eyelid(left_current, smooth=True, duration=duration * 0.6)
        self.set_right_eyelid(right_current, smooth=True, duration=duration * 0.6)

    def wink(self, eye='left', duration=0.25):
        """
        Wink one eye (perfect for sarcasm delivery!)

        Args:
            eye: 'left' or 'right'
            duration: Wink duration
        """
        if eye == 'left':
            current = self.current_left
            self.set_left_eyelid(0, smooth=True, duration=duration * 0.4)
            time.sleep(duration * 0.4)
            self.set_left_eyelid(current, smooth=True, duration=duration * 0.6)
        else:  # right
            current = self.current_right
            self.set_right_eyelid(0, smooth=True, duration=duration * 0.4)
            time.sleep(duration * 0.4)
            self.set_right_eyelid(current, smooth=True, duration=duration * 0.6)

        logger.debug(f"Winked {eye} eye")

    def eyebrow_raise(self, side='both', height=15):
        """
        Simulate eyebrow raise (open eyelids wider + will sync with eye ring top pixels)

        Args:
            side: 'left', 'right', or 'both'
            height: Additional degrees to open
        """
        if side in ['left', 'both']:
            target = min(90, self.current_left + height)
            self.set_left_eyelid(target, smooth=True, duration=0.2)

        if side in ['right', 'both']:
            target = min(90, self.current_right + height)
            self.set_right_eyelid(target, smooth=True, duration=0.2)

        logger.debug(f"Eyebrow raise: {side}")

    def double_take(self):
        """
        Quick look away and back (surprise reaction)
        """
        left_current = self.current_left
        right_current = self.current_right

        # Look away (narrow eyes)
        self.set_left_eyelid(max(0, left_current - 20), smooth=True, duration=0.15)
        self.set_right_eyelid(max(0, right_current - 20), smooth=True, duration=0.15)
        time.sleep(0.1)

        # Snap back (wide)
        self.set_left_eyelid(min(90, left_current + 10), smooth=True, duration=0.1)
        self.set_right_eyelid(min(90, right_current + 10), smooth=True, duration=0.1)
        time.sleep(0.15)

        # Return to normal
        self.set_left_eyelid(left_current, smooth=True, duration=0.2)
        self.set_right_eyelid(right_current, smooth=True, duration=0.2)

        logger.debug("Double take reaction")

    def micro_expression(self, expression_type='surprise', duration=0.3):
        """
        Brief expression flash for subtle reactions

        Args:
            expression_type: 'surprise', 'disapproval', 'interest', 'skeptical'
            duration: How long to hold micro-expression
        """
        # Store current state
        left_current = self.current_left
        right_current = self.current_right
        mouth_current = self.current_mouth

        # Apply micro-expression
        if expression_type == 'surprise':
            self.set_left_eyelid(min(90, left_current + 15), smooth=False)
            self.set_right_eyelid(min(90, right_current + 15), smooth=False)
            self.set_mouth(min(60, mouth_current + 10), smooth=False)
        elif expression_type == 'disapproval':
            self.set_left_eyelid(max(0, left_current - 10), smooth=False)
            self.set_right_eyelid(left_current, smooth=False)  # Asymmetric
            self.set_mouth(max(0, mouth_current - 3), smooth=False)
        elif expression_type == 'interest':
            self.set_left_eyelid(min(90, left_current + 8), smooth=False)
            self.set_right_eyelid(min(90, right_current + 12), smooth=False)  # Asymmetric
        elif expression_type == 'skeptical':
            self.set_left_eyelid(max(0, left_current - 5), smooth=False)
            self.set_right_eyelid(max(0, right_current - 5), smooth=False)
            self.set_mouth(max(0, mouth_current - 2), smooth=False)

        time.sleep(duration)

        # Return to previous
        self.set_left_eyelid(left_current, smooth=True, duration=0.2)
        self.set_right_eyelid(right_current, smooth=True, duration=0.2)
        self.set_mouth(mouth_current, smooth=True, duration=0.2)

        logger.debug(f"Micro-expression: {expression_type}")

    def set_expression(self, expression_name):
        """
        Set servo positions based on expression

        Expressions defined in config/expressions.yaml
        """
        expr_config = self.config.get('expressions', {})

        # Load expression definitions
        expr_path = Path(__file__).parent.parent / 'config' / 'expressions.yaml'
        with open(expr_path, 'r') as f:
            expressions = yaml.safe_load(f)

        if expression_name not in expressions['expressions']:
            logger.warning(f"Unknown expression: {expression_name}")
            return

        expr = expressions['expressions'][expression_name]
        eyelids = expr.get('eyelids', {})
        mouth = expr.get('mouth', {})

        # Set eyelids
        if 'left' in eyelids:
            self.set_left_eyelid(eyelids['left'])
        if 'right' in eyelids:
            self.set_right_eyelid(eyelids['right'])

        # Set mouth
        if 'angle' in mouth:
            self.set_mouth(mouth['angle'])

        logger.info(f"Expression set: {expression_name}")

    def start_speech_animation(self, base_amplitude: float = 0.3):
        """
        Start animating mouth during speech

        Args:
            base_amplitude: Base amplitude for mouth movement (0.0-1.0)
        """
        if self.speech_animation_active:
            logger.debug("Speech animation already active")
            return

        self.speech_animation_active = True
        self._speech_animation_thread = threading.Thread(
            target=self._speech_animation_loop,
            args=(base_amplitude,),
            daemon=True
        )
        self._speech_animation_thread.start()
        logger.debug("Speech animation started")

    def stop_speech_animation(self):
        """Stop mouth animation and return to neutral"""
        if not self.speech_animation_active:
            return

        self.speech_animation_active = False

        # Wait for thread to finish
        if self._speech_animation_thread:
            self._speech_animation_thread.join(timeout=1.0)

        # Return mouth to neutral
        self.set_mouth(self.mouth_config['neutral_angle'], smooth=True, duration=0.3)
        logger.debug("Speech animation stopped")

    def _speech_animation_loop(self, base_amplitude: float):
        """
        Animate mouth during speech with natural talking motion

        Args:
            base_amplitude: Base amplitude for mouth movement
        """
        neutral = self.mouth_config['neutral_angle']
        max_open = self.mouth_config['max_angle']

        # Calculate movement range
        mouth_range = int((max_open - neutral) * base_amplitude)

        frame = 0
        while self.speech_animation_active:
            # Create natural talking motion using sine wave with variation
            # Use multiple frequencies for more natural movement
            primary_wave = math.sin(frame * 0.5)  # Primary talking motion
            secondary_wave = math.sin(frame * 0.3) * 0.3  # Secondary variation
            noise = random.uniform(-0.1, 0.1)  # Small random variation

            # Combine waves
            combined = (primary_wave + secondary_wave + noise) * 0.5 + 0.5  # Normalize to 0-1

            # Calculate mouth position
            mouth_pos = neutral + int(mouth_range * combined)
            mouth_pos = max(neutral, min(max_open, mouth_pos))  # Clamp

            # Set mouth position (fast, no smoothing for responsive animation)
            with self.movement_lock:
                self.set_mouth(mouth_pos, smooth=False)

            frame += 1
            time.sleep(0.05)  # 20 FPS animation

    def cleanup(self):
        """Clean up GPIO resources"""
        # Stop any active animations
        self.stop_speech_animation()

        self.left_eyelid.close()
        self.right_eyelid.close()
        self.mouth.close()
        logger.info("Servo controller cleaned up")


# =============================================================================
# TESTING
# =============================================================================

def test_servos():
    """Test all servos through full range"""
    logger.info("Starting servo test...")

    controller = ServoController()

    try:
        # Test left eyelid
        logger.info("Testing left eyelid...")
        for angle in range(0, 91, 10):
            controller.set_left_eyelid(angle)
            time.sleep(0.2)

        # Test right eyelid
        logger.info("Testing right eyelid...")
        for angle in range(0, 91, 10):
            controller.set_right_eyelid(angle)
            time.sleep(0.2)

        # Test mouth
        logger.info("Testing mouth...")
        for angle in range(0, 61, 10):
            controller.set_mouth(angle)
            time.sleep(0.2)

        # Test blink
        logger.info("Testing blink...")
        for _ in range(3):
            controller.blink()
            time.sleep(0.5)

        # Test expressions
        logger.info("Testing expressions...")
        expressions = ['idle', 'listening', 'thinking', 'alert', 'happy', 'sarcasm']
        for expr in expressions:
            logger.info(f"Expression: {expr}")
            controller.set_expression(expr)
            time.sleep(1.5)

        # Reset
        controller.reset_to_neutral()
        logger.info("Servo test complete!")

    except KeyboardInterrupt:
        logger.info("Test interrupted")
    finally:
        controller.cleanup()


if __name__ == "__main__":
    test_servos()
