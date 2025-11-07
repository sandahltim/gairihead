#!/usr/bin/env python3
"""
Expression Engine - Manages GairiHead's emotional state and physical expressions

Coordinates servos, NeoPixels, and behaviors based on current state

v2.0 - Enhanced with:
- Contextual memory (last 3 expressions)
- Mood drift (emotional persistence)
- Personality quirks (TARS character)
- Micro-expressions
- Special modes
"""

import yaml
import time
import random
import threading
from collections import deque
from pathlib import Path
from loguru import logger

class ExpressionEngine:
    """Manages emotional state and coordinates hardware for expressions"""

    def __init__(self, config_path='/home/tim/GairiHead/config'):
        """
        Initialize expression engine

        Args:
            config_path: Path to config directory
        """
        self.config_path = Path(config_path)
        self.current_expression = 'idle'
        self.previous_expression = None
        self.state_lock = threading.Lock()

        # Load configurations
        self.load_configs()

        # Hardware controllers (initialized externally)
        self.servo_controller = None
        self.neopixel_controller = None
        self.arduino_display = None

        # State tracking
        self.is_speaking = False
        self.is_listening = False
        self.attention_target = None  # (x, y) face position

        # Autonomous behaviors
        self.last_blink = time.time()
        self.blink_interval = self.config.get('expressions', {}).get('blink_interval', 8000) / 1000.0
        self.idle_timeout = self.config.get('performance', {}).get('idle_timeout', 300000) / 1000.0
        self.last_activity = time.time()

        # === NEW v2.0 FEATURES ===

        # Contextual memory (last 3 expressions for mood tracking)
        self.expression_history = deque(maxlen=3)

        # Mood drift configuration
        self.mood_persistence = 0.3  # 30% chance to drift back to recent mood
        self.mood_map = {
            # Expression -> Related moods that can drift
            'sarcasm': ['amused', 'deadpan', 'unimpressed'],
            'happy': ['amused', 'pride', 'celebration'],
            'frustrated': ['concerned', 'skeptical', 'bored'],
            'alert': ['intrigued', 'surprised', 'concerned'],
            'thinking': ['processing', 'calculating', 'deep_focus'],
        }

        # Personality quirks (TARS character)
        self.personality_quirks_enabled = True
        self.quirk_probability = {
            'wink_after_sarcasm': 0.15,  # 15% chance
            'sigh_when_idle': 0.05,      # 5% chance per update
            'random_micro_expression': 0.02,  # 2% chance
        }

        # Interaction tracking
        self.interaction_count = 0
        self.repeated_query_count = 0  # Track if user asks same thing
        self.is_morning_grumpy = False  # Set based on time of day

        logger.info(f"ExpressionEngine v2.0 initialized with {len(self.expressions)} expressions")

    def load_configs(self):
        """Load configuration files"""
        # Main config
        config_file = self.config_path / 'gairi_head.yaml'
        with open(config_file, 'r') as f:
            self.config = yaml.safe_load(f)

        # Expressions config
        expr_file = self.config_path / 'expressions.yaml'
        with open(expr_file, 'r') as f:
            expr_config = yaml.safe_load(f)
            self.expressions = expr_config['expressions']
            self.transition_speed = expr_config.get('transition_speed', 300) / 1000.0

    def set_controllers(self, servo_controller=None, neopixel_controller=None, arduino_display=None):
        """
        Set hardware controllers

        Args:
            servo_controller: ServoController instance
            neopixel_controller: NeoPixelController instance
            arduino_display: ArduinoDisplay instance
        """
        if servo_controller:
            self.servo_controller = servo_controller
            logger.debug("Servo controller attached")

        if neopixel_controller:
            self.neopixel_controller = neopixel_controller
            logger.debug("NeoPixel controller attached")

        if arduino_display:
            self.arduino_display = arduino_display
            logger.debug("Arduino display attached")

    def set_expression(self, expression_name, force=False, trigger_quirks=True):
        """
        Set current expression with personality quirks

        Args:
            expression_name: Name of expression from expressions.yaml
            force: Force expression even if already set
            trigger_quirks: Allow personality quirks to trigger

        Returns:
            bool: True if expression changed
        """
        with self.state_lock:
            if not force and expression_name == self.current_expression:
                return False

            if expression_name not in self.expressions:
                logger.warning(f"Unknown expression: {expression_name}")
                return False

            # Add to history before changing
            self.expression_history.append(self.current_expression)

            self.previous_expression = self.current_expression
            self.current_expression = expression_name
            self.last_activity = time.time()
            self.interaction_count += 1

            logger.info(f"Expression: {self.previous_expression} → {self.current_expression}")

            # Apply to hardware
            self._apply_expression()

            # Trigger personality quirks
            if trigger_quirks and self.personality_quirks_enabled:
                self._trigger_personality_quirks()

            return True

    def _get_current_state(self):
        """Get current system state as string"""
        if self.is_speaking:
            return "speaking"
        elif self.is_listening:
            return "listening"
        else:
            return self.current_expression

    def _apply_expression(self):
        """Apply current expression to hardware"""
        expr = self.expressions[self.current_expression]

        # Servos
        if self.servo_controller:
            if 'left_eyelid' in expr:
                self.servo_controller.set_left_eyelid(expr['left_eyelid'])
            if 'right_eyelid' in expr:
                self.servo_controller.set_right_eyelid(expr['right_eyelid'])
            if 'mouth' in expr:
                self.servo_controller.set_mouth(expr['mouth'])

        # NeoPixels
        if self.neopixel_controller and 'eyes' in expr:
            eye_color = expr['eyes']
            if isinstance(eye_color, list) and len(eye_color) == 3:
                self.neopixel_controller.set_color(eye_color)
            elif isinstance(eye_color, str):
                # Named color or animation
                self.neopixel_controller.set_animation(eye_color)

        # Arduino Display
        if self.arduino_display and self.arduino_display.connected:
            # Send expression update to display
            self.arduino_display.update_status(
                expression=self.current_expression,
                state=self._get_current_state()
            )

    def start_speaking(self):
        """Indicate GairiHead is speaking"""
        self.is_speaking = True
        self.set_expression('listening')  # Keep eyes open while talking
        logger.debug("Speaking started")

    def stop_speaking(self):
        """Indicate GairiHead stopped speaking"""
        self.is_speaking = False
        self.return_to_idle()
        logger.debug("Speaking stopped")

    def start_listening(self):
        """Indicate GairiHead is listening"""
        self.is_listening = True
        self.set_expression('listening')
        logger.debug("Listening started")

    def stop_listening(self):
        """Indicate GairiHead stopped listening"""
        self.is_listening = False
        self.return_to_idle()
        logger.debug("Listening stopped")

    def thinking(self, level='normal'):
        """
        Show thinking expression

        Args:
            level: 'normal' or 'deep'
        """
        if level == 'deep':
            self.set_expression('processing')
        else:
            self.set_expression('thinking')

    def react(self, emotion):
        """
        React with emotion

        Args:
            emotion: One of: happy, surprised, confused, frustrated, sarcasm, alert, error
        """
        if emotion in self.expressions:
            self.set_expression(emotion)
            # Return to previous state after reaction
            threading.Timer(2.0, self.return_to_idle).start()
        else:
            logger.warning(f"Unknown emotion: {emotion}")

    def return_to_idle(self):
        """
        Return to appropriate idle state with mood drift
        """
        if self.is_speaking or self.is_listening:
            return  # Don't interrupt active states

        # Check for mood drift
        drift_expr = self._get_mood_drift_expression()
        if drift_expr:
            logger.debug(f"Mood drift to {drift_expr} (from recent {list(self.expression_history)})")
            self.set_expression(drift_expr)
            return

        # Check if should enter low power
        time_idle = time.time() - self.last_activity
        if time_idle > self.idle_timeout:
            self.set_expression('sleeping')  # Fixed: was 'sleepy', now consistent
        else:
            self.set_expression('idle')

    def blink(self):
        """Perform a blink"""
        if self.servo_controller:
            self.servo_controller.blink()
            self.last_blink = time.time()

    def update(self):
        """
        Update autonomous behaviors (call from main loop)

        Should be called every ~100ms
        """
        # Autonomous blinking (with natural variation)
        if time.time() - self.last_blink > self.blink_interval:
            if not self.is_speaking:  # Don't blink while talking
                self.blink()
                # Vary next blink interval slightly for naturalness
                base = self.config.get('expressions', {}).get('blink_interval', 8000) / 1000.0
                self.blink_interval = base * random.uniform(0.8, 1.2)

        # Random micro-expressions for liveliness
        if (self.personality_quirks_enabled and
            random.random() < self.quirk_probability['random_micro_expression']):
            if not (self.is_speaking or self.is_listening):
                reactions = ['interest', 'skeptical', 'disapproval']
                self.micro_reaction(random.choice(reactions))

        # Idle timeout
        time_idle = time.time() - self.last_activity
        if time_idle > self.idle_timeout and self.current_expression != 'sleeping':
            if not (self.is_speaking or self.is_listening):
                self.set_expression('sleeping')

    def look_at(self, x, y):
        """
        Look at a position (future: eye tracking with camera)

        Args:
            x: Horizontal position (-1.0 to 1.0, center is 0)
            y: Vertical position (-1.0 to 1.0, center is 0)
        """
        self.attention_target = (x, y)
        self.last_activity = time.time()

        # TODO: Implement eye tracking with servos
        # For now, just ensure eyes are open
        if self.current_expression in ['sleepy', 'idle']:
            self.set_expression('alert')

    def get_state(self):
        """
        Get current state

        Returns:
            dict: Current state information
        """
        return {
            'expression': self.current_expression,
            'previous_expression': self.previous_expression,
            'is_speaking': self.is_speaking,
            'is_listening': self.is_listening,
            'attention_target': self.attention_target,
            'time_since_activity': time.time() - self.last_activity,
            'expression_history': list(self.expression_history),
            'interaction_count': self.interaction_count
        }

    # =========================================================================
    # PERSONALITY QUIRKS & MOOD MANAGEMENT (v2.0)
    # =========================================================================

    def _trigger_personality_quirks(self):
        """
        Trigger personality quirks based on current expression

        Examples:
        - Wink after delivering sarcasm
        - Sigh when returning to idle
        """
        if not self.servo_controller:
            return

        # Wink after sarcasm delivery (TARS personality!)
        if (self.current_expression == 'sarcasm' and
            random.random() < self.quirk_probability['wink_after_sarcasm']):
            # Delay slightly, then wink
            threading.Timer(0.5, lambda: self.servo_controller.wink('right')).start()
            logger.debug("Quirk: Wink after sarcasm")

        # Occasional sigh when idle (boredom)
        elif (self.current_expression == 'idle' and
              random.random() < self.quirk_probability['sigh_when_idle']):
            threading.Timer(1.0, self.sigh).start()
            logger.debug("Quirk: Sigh when idle")

    def _get_mood_drift_expression(self):
        """
        Get expression to drift to based on mood persistence

        Returns:
            str: Expression name or None
        """
        if not self.expression_history:
            return None

        # Check recent history for mood patterns
        recent = list(self.expression_history)[-2:]  # Last 2 expressions

        for expr in recent:
            if expr in self.mood_map:
                if random.random() < self.mood_persistence:
                    # Drift to related mood
                    drift_options = self.mood_map[expr]
                    return random.choice(drift_options)

        return None

    def micro_reaction(self, reaction_type='surprise'):
        """
        Quick micro-expression reaction

        Args:
            reaction_type: 'surprise', 'disapproval', 'interest', 'skeptical'
        """
        if self.servo_controller:
            self.servo_controller.micro_expression(reaction_type, duration=0.25)
            logger.debug(f"Micro-reaction: {reaction_type}")

    def sigh(self):
        """
        Perform a sigh (eyelids droop, slight mouth downturn)
        """
        if not self.servo_controller:
            return

        # Store current
        current_left = self.servo_controller.current_left
        current_right = self.servo_controller.current_right

        # Droop
        self.servo_controller.set_left_eyelid(max(0, current_left - 15),
                                              smooth=True, duration=0.4)
        self.servo_controller.set_right_eyelid(max(0, current_right - 15),
                                               smooth=True, duration=0.4)
        time.sleep(0.5)

        # Return
        self.servo_controller.set_left_eyelid(current_left, smooth=True, duration=0.6)
        self.servo_controller.set_right_eyelid(current_right, smooth=True, duration=0.6)

        logger.debug("Sigh")

    def check_time_of_day_mood(self):
        """
        Check time of day and adjust mood accordingly

        Morning (5-9am): Slightly grumpy
        Afternoon (2-4pm): Planning time energy
        Evening (6-10pm): Relaxed
        """
        import datetime
        now = datetime.datetime.now()
        hour = now.hour

        # Morning grumpy mode (slower to react)
        if 5 <= hour < 9:
            self.is_morning_grumpy = True
            self.blink_interval *= 1.2  # Slower blinks
        else:
            self.is_morning_grumpy = False

        # Thursday 2pm planning energy
        if now.weekday() == 3 and hour == 14:  # Thursday
            self.set_expression('intrigued')

    def celebration_mode(self, duration=3.0):
        """
        Celebration animation with rainbow eyes

        Args:
            duration: How long to celebrate
        """
        self.set_expression('celebration', trigger_quirks=False)
        time.sleep(duration)
        self.return_to_idle()

    def demo_mode(self):
        """
        Cycle through all expressions for demonstration
        """
        logger.info("Starting demo mode - cycling all expressions")

        demo_sequence = [
            'idle', 'listening', 'thinking', 'processing',
            'happy', 'amused', 'pride', 'celebration',
            'alert', 'surprised', 'intrigued', 'concerned',
            'sarcasm', 'deadpan', 'unimpressed', 'disapproval',
            'skeptical', 'confused', 'bored', 'frustrated',
            'error', 'sheepish'
        ]

        for expr in demo_sequence:
            if expr in self.expressions:
                logger.info(f"Demo: {expr}")
                self.set_expression(expr, trigger_quirks=False)
                time.sleep(1.5)

        self.set_expression('idle')
        logger.info("Demo mode complete")

    def cleanup(self):
        """Cleanup resources"""
        logger.info("ExpressionEngine cleanup")
        # Return to neutral expression
        self.set_expression('idle', trigger_quirks=False)


# Example usage and testing
if __name__ == '__main__':
    from loguru import logger
    import sys

    # Configure logging
    logger.remove()
    logger.add(sys.stderr, level="DEBUG")

    print("ExpressionEngine Test")
    print("=" * 60)

    # Initialize engine
    engine = ExpressionEngine()

    # Test state transitions
    print("\nTesting expressions:")
    for expr in ['idle', 'listening', 'thinking', 'alert', 'happy', 'sarcasm']:
        print(f"  → {expr}")
        engine.set_expression(expr)
        time.sleep(1)

    # Test reactions
    print("\nTesting reactions:")
    engine.react('surprised')
    time.sleep(0.5)

    # Test state tracking
    print("\nTesting state tracking:")
    engine.start_listening()
    print(f"  State: {engine.get_state()}")
    time.sleep(1)
    engine.stop_listening()

    # Test autonomous updates
    print("\nTesting autonomous behaviors:")
    for i in range(5):
        engine.update()
        time.sleep(0.5)

    print("\n✅ ExpressionEngine test complete")
    engine.cleanup()
