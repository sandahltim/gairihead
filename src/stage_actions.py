#!/usr/bin/env python3
"""
Stage Actions Module for GairiHead
Handles stage direction actions from Gary's metadata responses
Maps action metadata to physical actions (servos, LEDs, sound effects, pauses)
Gary strips markers from text and sends: {"response": "text", "emotion": "X", "actions": [...]}
"""

import asyncio
import time
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any
from loguru import logger
import sounddevice as sd
import soundfile as sf


class StageActionHandler:
    """Handles stage direction actions from Gary's metadata responses"""

    def __init__(self, sounds_dir: Optional[Path] = None, servo_controller=None, expression_engine=None):
        """
        Initialize stage action handler

        Args:
            sounds_dir: Directory containing sound effect files
            servo_controller: ServoController instance for physical actions
            expression_engine: ExpressionEngine instance for LED patterns
        """
        self.sounds_dir = sounds_dir or Path(__file__).parent.parent / 'sounds'
        self.sounds_dir.mkdir(exist_ok=True)

        # Controllers for physical actions
        self.servo_controller = servo_controller
        self.expression_engine = expression_engine

        # Sound effects cache {action_name: (audio_data, sample_rate)}
        self.sound_cache: Dict[str, Tuple[np.ndarray, int]] = {}

        # Load sound effects
        self._load_sound_effects()

        logger.info(f"StageActionHandler initialized (sounds: {self.sounds_dir})")

    def _load_sound_effects(self):
        """Load all available sound effect files into cache"""
        sound_files = list(self.sounds_dir.glob('*.wav')) + list(self.sounds_dir.glob('*.mp3'))

        for sound_file in sound_files:
            try:
                audio_data, sample_rate = sf.read(str(sound_file))
                # Convert to mono if stereo
                if len(audio_data.shape) > 1:
                    audio_data = np.mean(audio_data, axis=1)

                # Normalize to prevent clipping
                audio_data = audio_data.astype(np.float32)
                if np.max(np.abs(audio_data)) > 0:
                    audio_data = audio_data / np.max(np.abs(audio_data)) * 0.8

                # Cache by marker name (filename without extension)
                marker_name = sound_file.stem
                self.sound_cache[marker_name] = (audio_data, sample_rate)
                logger.debug(f"Loaded sound effect: {marker_name} ({len(audio_data)} samples, {sample_rate}Hz)")
            except Exception as e:
                logger.warning(f"Failed to load sound effect {sound_file}: {e}")

        logger.info(f"Loaded {len(self.sound_cache)} sound effects")

    async def process_actions_metadata(self, actions: List[Any]) -> None:
        """
        Process actions metadata from Gary's response
        Gary sends: {"response": "text", "emotion": "X", "actions": ["wink", "pause:500", ...]}

        Args:
            actions: List of action strings/objects from Gary's metadata
        """
        if not actions:
            return

        logger.info(f"🎬 Processing {len(actions)} actions from Gary's metadata")

        for action in actions:
            try:
                # Parse action (can be string like "wink" or "pause:500")
                if isinstance(action, str):
                    await self.execute_action(action)
                elif isinstance(action, dict):
                    # Handle dict format: {"type": "pause", "duration": 500}
                    action_type = action.get('type', '')
                    params = action.get('params', {})
                    await self.execute_action(action_type, params)
                else:
                    logger.warning(f"Unknown action format: {action}")
            except Exception as e:
                logger.error(f"Failed to execute action {action}: {e}")

    async def execute_action(self, action: str, params: Optional[Dict] = None) -> bool:
        """
        Execute a single action (wink, blink, pause, sound effect, LED pattern)

        Args:
            action: Action name (e.g., "wink", "pause:500", "chuckle", "sighs")
            params: Optional parameters dict

        Returns:
            True if executed successfully
        """
        params = params or {}

        # Parse action:params format (e.g., "pause:500")
        if ':' in action:
            action, param_value = action.split(':', 1)
            action = action.strip()
            params['value'] = param_value

        action = action.lower().strip()
        logger.debug(f"Executing action: {action} (params: {params})")

        # === QUICK WIN #1: Winks & Blinks (5 minutes) ===
        if action in ['wink', 'winks']:
            return await self._action_wink()
        elif action in ['blink', 'blinks']:
            return await self._action_blink()

        # === QUICK WIN #2: Chuckle/LED patterns (30 minutes) ===
        elif action in ['chuckle', 'chuckles', 'excited', 'eyes_light_up']:
            return await self._action_led_pattern(action)

        # === QUICK WIN #3: Pauses (1 hour) ===
        elif action in ['pause', 'dramatic_pause', 'brief_pause']:
            duration = params.get('value', params.get('duration', 500))
            return await self._action_pause(int(duration))

        # === QUICK WIN #4: Sound effects (30 minutes) ===
        elif action in ['sigh', 'sighs', 'gasp', 'gasps', 'laugh', 'laughs',
                       'breath', 'groan', 'groans', 'yawn', 'yawns', 'snicker', 'snickers']:
            return self._action_sound_effect(action)

        # === Other physical actions ===
        elif action in ['nods', 'nod']:
            return await self._action_nod()
        elif action in ['shake_head', 'shakes_head']:
            return await self._action_shake_head()

        else:
            logger.warning(f"Unknown action: {action}")
            return False

    # ========== ACTION IMPLEMENTATIONS ==========

    async def _action_wink(self) -> bool:
        """QUICK WIN #1: Wink one eye (5 minutes to implement)"""
        if not self.servo_controller:
            logger.warning("Cannot wink - no servo controller")
            return False

        try:
            logger.info("😉 Winking right eye")
            # Close right eye, keep left open
            original_right = self.servo_controller.current_right
            self.servo_controller.right_eyelid.value = self.servo_controller.angle_to_servo_value_right_eye(0)
            await asyncio.sleep(0.15)  # 150ms wink
            # Reopen
            self.servo_controller.right_eyelid.value = self.servo_controller.angle_to_servo_value_right_eye(original_right)
            return True
        except Exception as e:
            logger.error(f"Wink failed: {e}")
            return False

    async def _action_blink(self) -> bool:
        """Quick blink both eyes"""
        if not self.servo_controller:
            logger.warning("Cannot blink - no servo controller")
            return False

        try:
            logger.debug("Blinking both eyes")
            original_left = self.servo_controller.current_left
            original_right = self.servo_controller.current_right

            # Close both
            self.servo_controller.left_eyelid.value = self.servo_controller.angle_to_servo_value_left_eye(0)
            self.servo_controller.right_eyelid.value = self.servo_controller.angle_to_servo_value_right_eye(0)
            await asyncio.sleep(0.1)  # 100ms blink

            # Reopen
            self.servo_controller.left_eyelid.value = self.servo_controller.angle_to_servo_value_left_eye(original_left)
            self.servo_controller.right_eyelid.value = self.servo_controller.angle_to_servo_value_right_eye(original_right)
            return True
        except Exception as e:
            logger.error(f"Blink failed: {e}")
            return False

    async def _action_led_pattern(self, pattern_name: str) -> bool:
        """
        QUICK WIN #2: LED emotion patterns (30 minutes)
        chuckle → sparkle/yellow, excited → rainbow, eyes_light_up → bright flash
        """
        if not self.expression_engine:
            logger.warning("Cannot set LED pattern - no expression engine")
            return False

        try:
            # Map action to expression
            expression_map = {
                'chuckle': 'amused',      # Soft green, smile animation
                'chuckles': 'amused',
                'excited': 'celebration',  # Gold, rainbow animation
                'eyes_light_up': 'surprised',  # Bright white flash, expand pulse
            }

            expression = expression_map.get(pattern_name, 'happy')
            logger.info(f"💡 Setting LED pattern for '{pattern_name}' → expression '{expression}'")
            self.expression_engine.set_expression(expression)
            return True
        except Exception as e:
            logger.error(f"LED pattern failed: {e}")
            return False

    async def _action_pause(self, duration_ms: int) -> bool:
        """
        QUICK WIN #3: Pause/silence insertion (1 hour)
        Inserts silence in TTS output for dramatic effect
        """
        duration_sec = duration_ms / 1000.0
        logger.info(f"⏸️  Pausing for {duration_ms}ms")
        await asyncio.sleep(duration_sec)
        return True

    def _action_sound_effect(self, sound_name: str) -> bool:
        """
        QUICK WIN #4: Sound effects (30 minutes)
        Play sound file for sighs, gasps, laughs, etc.
        """
        # Normalize sound name (sighs → sigh)
        sound_map = {
            'sighs': 'sigh',
            'gasps': 'gasp',
            'laughs': 'laugh',
            'chuckles': 'chuckle',
            'groans': 'groan',
            'yawns': 'yawn',
            'snickers': 'snicker',
        }
        canonical_name = sound_map.get(sound_name, sound_name)

        return self.play_sound_effect(canonical_name)

    async def _action_nod(self) -> bool:
        """Nod head up/down (future: need head tilt servo)"""
        logger.warning("Nod action not implemented - requires head tilt servo")
        return False

    async def _action_shake_head(self) -> bool:
        """Shake head left/right (future: need head pan servo)"""
        logger.warning("Shake head action not implemented - requires head pan servo")
        return False

    def play_sound_effect(self, sound_name: str, volume: float = 0.7) -> bool:
        """
        Play a sound effect

        Args:
            sound_name: Name of sound effect (e.g., 'sigh', 'gasp')
            volume: Playback volume 0.0-1.0

        Returns:
            True if played successfully
        """
        if sound_name not in self.sound_cache:
            logger.warning(f"Sound effect '{sound_name}' not found in cache")
            return False

        try:
            audio_data, sample_rate = self.sound_cache[sound_name]

            # Apply volume
            audio_with_volume = audio_data * volume

            logger.info(f"🔊 Playing sound effect: {sound_name}")
            sd.play(audio_with_volume, samplerate=sample_rate)
            sd.wait()  # Wait for playback to finish

            return True
        except Exception as e:
            logger.error(f"Failed to play sound effect '{sound_name}': {e}")
            return False

    def insert_pause_in_audio(self, audio: np.ndarray, sample_rate: int,
                              pause_duration: float) -> np.ndarray:
        """
        Insert silence pause into audio array (utility for TTS pause insertion)

        Args:
            audio: Audio data (numpy array)
            sample_rate: Sample rate in Hz
            pause_duration: Duration of pause in seconds

        Returns:
            Audio with pause inserted
        """
        pause_samples = int(sample_rate * pause_duration)
        silence = np.zeros(pause_samples, dtype=audio.dtype)

        # Insert pause at end (for simplicity)
        # TODO: Could parse action timing and insert mid-audio
        return np.concatenate([audio, silence])


# Standalone test function
async def test_stage_actions():
    """Test stage action metadata processing"""
    print("="*70)
    print("STAGE ACTIONS METADATA TEST")
    print("="*70)

    handler = StageActionHandler()

    # Test action metadata from Gary
    test_scenarios = [
        {
            "response": "Well, that's not good.",
            "emotion": "concerned",
            "actions": ["pause:1000", "sighs"]
        },
        {
            "response": "Oh, that's brilliant.",
            "emotion": "sarcasm",
            "actions": ["wink", "chuckle"]
        },
        {
            "response": "Let me think about that. No.",
            "emotion": "deadpan",
            "actions": ["pause:500", "blink"]
        },
        {
            "response": "Alright, here's what we'll do.",
            "emotion": "thinking",
            "actions": ["breath", "excited"]
        },
        {
            "response": "You did WHAT?",
            "emotion": "surprised",
            "actions": ["gasp", "eyes_light_up"]
        }
    ]

    for scenario in test_scenarios:
        print(f"\n{'='*70}")
        print(f"Response: {scenario['response']}")
        print(f"Emotion:  {scenario['emotion']}")
        print(f"Actions:  {scenario['actions']}")
        print(f"{'='*70}")

        # Process actions
        await handler.process_actions_metadata(scenario['actions'])

    print("\n" + "="*70)
    print("TEST COMPLETE")
    print("="*70)


if __name__ == '__main__':
    import asyncio
    asyncio.run(test_stage_actions())
