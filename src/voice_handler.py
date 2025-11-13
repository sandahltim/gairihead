#!/usr/bin/env python3
"""
Voice Handler - Hardware voice I/O for GairiHead (routes intelligence to Gary)

ARCHITECTURE (Clarified):
- GairiHead = Hardware Interface (THIS CODE - mic, speaker, audio processing)
- Gary Server = ALL Intelligence (STT via faster-whisper, LLM tiers)
- This module: Capture audio → Send to Gary → Receive response → Speak

Version: 1.0 (2025-11-07)
Purpose: Complete voice I/O pipeline for GairiHead physical robot

Components:
- Audio Capture: sounddevice (C920 microphone) + VAD-based silence detection
- Speech-to-Text: Gary's faster-whisper (primary), local Whisper fallback
- LLM Processing: Gary's Qwen/Haiku tiers (via LLMTierManager routing)
- Text-to-Speech: Piper neural TTS "joe" voice (local, audio-reactive mouth)

Flow:
1. Record audio from microphone (VAD-based stop detection)
2. Send audio to Gary server via WebSocket
3. Gary transcribes (faster-whisper) + processes (Qwen/Haiku tiers)
4. Receive response from Gary
5. Speak response with Piper TTS + animate mouth

Core Principles Applied:
- #6: Trust but verify (test each component before integration)
- #8: Do it well (proper error handling, logging, fallbacks)
"""

import whisper
import sounddevice as sd
import numpy as np
import wave
import io
import time
import tempfile
import random
import yaml
from pathlib import Path
from loguru import logger
from typing import Optional, Dict, Tuple
import webrtcvad
from scipy import signal  # For pitch shifting

# Try to import Piper, fall back to pyttsx3 if not available
try:
    from piper import PiperVoice
    PIPER_AVAILABLE = True
except ImportError:
    PIPER_AVAILABLE = False
    import pyttsx3


class VoiceHandler:
    """Manages complete voice interaction pipeline"""

    def __init__(self, config, llm_tier_manager=None, arduino_display=None, expression_engine=None):
        """
        Initialize voice handler

        Args:
            config: Configuration dict from gairi_head.yaml
            llm_tier_manager: LLMTierManager instance for query processing
            arduino_display: ArduinoDisplay instance for visual feedback
            expression_engine: ExpressionEngine instance for servo expressions
        """
        self.config = config.get('voice', {})
        self.llm_manager = llm_tier_manager
        self.arduino_display = arduino_display
        self.expression_engine = expression_engine

        # Microphone settings
        self.sample_rate = self.config.get('microphone', {}).get('sample_rate', 16000)
        self.chunk_size = self.config.get('microphone', {}).get('chunk_size', 1024)
        self.device_index = self.config.get('microphone', {}).get('device_index', None)

        # VAD settings
        self.vad_enabled = self.config.get('vad', {}).get('enabled', True)
        self.vad_aggressiveness = self.config.get('vad', {}).get('aggressiveness', 3)  # 3 = most strict (filters noise better)
        self.vad_silence_duration = self.config.get('vad', {}).get('silence_duration', 1.5)
        self.vad_max_duration = self.config.get('vad', {}).get('max_duration', 30.0)

        # Whisper STT
        self.whisper_model = None
        self.whisper_model_name = self.config.get('stt', {}).get('model', 'tiny')
        self.use_remote_transcription = self.config.get('stt', {}).get('use_remote', True)

        # TTS settings
        self.tts_engine_type = self.config.get('tts', {}).get('engine', 'piper')
        self.tts_engine = None
        self.piper_voice = None
        self.tts_voice = self.config.get('tts', {}).get('voice', 'joe')
        self.tts_speed = self.config.get('tts', {}).get('speed', 1.0)
        self.tts_volume = self.config.get('tts', {}).get('volume', 0.8)
        self.tts_model_path = self.config.get('tts', {}).get('model_path', '/home/tim/GairiHead/data/piper_voices')

        # Load voice emotion mappings (v2.1 - emotion-based voice modulation)
        self.voice_emotions = self._load_voice_emotions()

        transcription_method = "Gary server (remote)" if self.use_remote_transcription else f"Local (Whisper {self.whisper_model_name})"
        tts_method = "Piper (neural)" if self.tts_engine_type == 'piper' and PIPER_AVAILABLE else "pyttsx3 (espeak)"
        vad_status = f"VAD enabled ({self.vad_silence_duration}s silence)" if self.vad_enabled else "Fixed duration"
        emotion_modulation = f"Enabled ({len(self.voice_emotions)} emotions)" if self.voice_emotions else "Disabled"
        logger.info(f"VoiceHandler v2.1 initialized (STT: {transcription_method}, TTS: {tts_method}, Recording: {vad_status}, Emotions: {emotion_modulation})")

        # Statistics
        self.stats = {
            'total_recordings': 0,
            'transcription_successes': 0,
            'transcription_failures': 0,
            'tts_successes': 0,
            'tts_failures': 0,
            'total_processing_time_ms': 0
        }

    def _load_voice_emotions(self) -> Dict:
        """
        Load voice emotion mappings from config/voice_emotions.yaml

        Returns:
            Dict of emotion -> {speed, volume, pitch_shift} mappings
        """
        try:
            config_path = Path(__file__).parent.parent / 'config' / 'voice_emotions.yaml'
            if not config_path.exists():
                logger.warning(f"⚠️ Voice emotions config not found: {config_path}")
                return {}

            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)

            emotions = config.get('voice_emotions', {})
            logger.debug(f"Loaded {len(emotions)} voice emotion mappings")
            return emotions

        except Exception as e:
            logger.error(f"❌ Failed to load voice emotions: {e}")
            return {}

    def _load_whisper_model(self):
        """Lazy load Whisper model (downloads on first use)"""
        if self.whisper_model is None:
            logger.info(f"Loading Whisper model '{self.whisper_model_name}'...")
            start = time.time()
            self.whisper_model = whisper.load_model(self.whisper_model_name)
            load_time = int((time.time() - start) * 1000)
            logger.success(f"✅ Whisper model loaded ({load_time}ms)")
        return self.whisper_model

    def _init_tts_engine(self):
        """Lazy initialize TTS engine (Piper or pyttsx3)"""
        if self.tts_engine is not None:
            return self.tts_engine

        if self.tts_engine_type == 'piper' and PIPER_AVAILABLE:
            logger.info(f"Initializing Piper TTS engine (voice: {self.tts_voice})...")
            try:
                # Load Piper voice model
                model_file = f"{self.tts_model_path}/en_US-{self.tts_voice}-medium.onnx"
                self.piper_voice = PiperVoice.load(model_file)
                self.tts_engine = 'piper'  # Just a marker
                logger.success(f"✅ Piper TTS initialized (voice: {self.tts_voice}, neural)")
                return self.tts_engine
            except Exception as e:
                logger.error(f"❌ Piper initialization failed: {e}, falling back to pyttsx3")
                # Fall through to pyttsx3

        # Fallback to pyttsx3
        logger.info("Initializing pyttsx3 TTS engine...")
        import pyttsx3
        self.tts_engine = pyttsx3.init()
        self.tts_engine.setProperty('rate', int(150 * self.tts_speed))
        self.tts_engine.setProperty('volume', self.tts_volume)
        logger.success(f"✅ pyttsx3 TTS initialized (rate: {int(150 * self.tts_speed)} WPM)")
        return self.tts_engine

    def record_audio(self, duration: float = 3.0, silence_threshold: float = 0.01) -> Optional[np.ndarray]:
        """
        Record audio from microphone (fixed duration - for backwards compatibility)

        Args:
            duration: Recording duration in seconds
            silence_threshold: RMS threshold to detect silence (auto-stop if silent)

        Returns:
            numpy array of audio samples (16kHz mono) or None if failed
        """
        try:
            self.stats['total_recordings'] += 1

            logger.info(f"🎤 Recording {duration}s of audio...")
            start_time = time.time()

            # Record audio
            recording = sd.rec(
                int(duration * self.sample_rate),
                samplerate=self.sample_rate,
                channels=1,
                dtype=np.float32,
                device=self.device_index
            )
            sd.wait()  # Wait for recording to complete

            # Calculate RMS to check if audio was captured
            rms = np.sqrt(np.mean(recording ** 2))
            record_time = int((time.time() - start_time) * 1000)

            if rms < silence_threshold:
                logger.warning(f"⚠️ Silent audio detected (RMS: {rms:.4f}, threshold: {silence_threshold})")
                return None

            logger.success(f"✅ Audio recorded ({record_time}ms, RMS: {rms:.4f})")
            return recording.squeeze()  # Remove extra dimensions

        except Exception as e:
            logger.error(f"❌ Audio recording failed: {e}")
            return None

    def record_audio_with_vad(self, max_duration: float = 30.0,
                              silence_duration: float = 1.5,
                              vad_aggressiveness: int = 2) -> Optional[np.ndarray]:
        """
        Record audio using Voice Activity Detection (VAD)
        Automatically stops recording when user stops speaking

        Args:
            max_duration: Maximum recording time in seconds (safety limit)
            silence_duration: Seconds of silence before stopping (e.g., 1.5s)
            vad_aggressiveness: VAD sensitivity 0-3 (0=liberal, 3=aggressive)

        Returns:
            numpy array of audio samples (16kHz mono) or None if failed
        """
        try:
            self.stats['total_recordings'] += 1

            # Initialize WebRTC VAD
            vad = webrtcvad.Vad(vad_aggressiveness)

            # VAD frame parameters (must be 10, 20, or 30ms)
            frame_duration_ms = 30  # 30ms frames
            frame_size = int(self.sample_rate * frame_duration_ms / 1000)  # samples per frame
            bytes_per_frame = frame_size * 2  # 16-bit = 2 bytes per sample

            # Recording state
            audio_buffer = []
            silence_frames = 0
            silence_threshold_frames = int(silence_duration * 1000 / frame_duration_ms)
            speech_detected = False
            speech_frames = 0  # Count consecutive speech frames
            min_speech_frames = 10  # Require ~300ms of speech to avoid false triggers from noise
            max_frames = int(max_duration * 1000 / frame_duration_ms)

            logger.info(f"🎤 Recording with VAD (stops after {silence_duration}s silence, max {max_duration}s)...")
            logger.info(f"   VAD aggressiveness: {vad_aggressiveness} (0=liberal, 3=strict)")
            logger.info("   Speak now...")
            start_time = time.time()

            # Start audio stream
            stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                dtype=np.int16,  # VAD requires 16-bit PCM
                device=self.device_index,
                blocksize=frame_size
            )
            stream.start()

            frame_count = 0
            try:
                while frame_count < max_frames:
                    # Read one frame
                    frame_data, overflowed = stream.read(frame_size)

                    if overflowed:
                        logger.warning("⚠️ Audio buffer overflow (processing too slow)")

                    # Convert to bytes for VAD
                    frame_bytes = frame_data.tobytes()

                    # Check if this frame contains speech
                    is_speech = vad.is_speech(frame_bytes, self.sample_rate)

                    if is_speech:
                        speech_frames += 1
                        silence_frames = 0

                        # Only mark as speech_detected after sustained speech (filters noise bursts)
                        if not speech_detected and speech_frames >= min_speech_frames:
                            logger.info(f"   🗣️ Speech detected ({speech_frames * frame_duration_ms}ms sustained), recording...")
                            speech_detected = True

                        # Always buffer if we've detected real speech
                        if speech_detected:
                            audio_buffer.append(frame_data)
                    else:
                        # Silence detected
                        if speech_detected:
                            # Only count silence after we've detected sustained speech
                            silence_frames += 1
                            audio_buffer.append(frame_data)  # Still collect during silence

                            # Stop if we've had enough silence
                            if silence_frames >= silence_threshold_frames:
                                logger.info(f"   Detected {silence_duration}s silence after speech, stopping...")
                                break
                        else:
                            # Silence before sustained speech - reset speech counter (was likely noise)
                            if speech_frames > 0:
                                logger.debug(f"   Brief noise burst ignored ({speech_frames * frame_duration_ms}ms)")
                            speech_frames = 0

                    frame_count += 1

            finally:
                stream.stop()
                stream.close()

            # Check if we got any speech
            if not speech_detected:
                logger.warning("⚠️ No speech detected")
                return None

            # Combine all frames into single numpy array
            if not audio_buffer:
                logger.warning("⚠️ No audio collected")
                return None

            # Concatenate all frames
            audio_int16 = np.concatenate(audio_buffer, axis=0).squeeze()

            # Convert to float32 (for compatibility with Whisper)
            audio_float32 = audio_int16.astype(np.float32) / 32768.0

            # Calculate stats
            record_time = int((time.time() - start_time) * 1000)
            duration_recorded = len(audio_float32) / self.sample_rate
            rms = np.sqrt(np.mean(audio_float32 ** 2))

            logger.success(f"✅ Audio recorded ({record_time}ms, {duration_recorded:.1f}s, RMS: {rms:.4f})")
            return audio_float32

        except Exception as e:
            logger.error(f"❌ VAD recording failed: {e}")
            return None

    def transcribe_audio(self, audio: np.ndarray, authorization: Optional[Dict] = None) -> Optional[str]:
        """
        Transcribe audio using remote (Gary) or local (Whisper)

        Args:
            audio: numpy array of audio samples (float32, 16kHz)
            authorization: Authorization context from face recognition (for Gary)

        Returns:
            Transcribed text or None if failed
        """
        try:
            # Use remote transcription via Gary (MUCH faster if available)
            if self.use_remote_transcription and self.llm_manager:
                logger.info("📝 Transcribing audio via Gary server...")
                start_time = time.time()

                text = self.llm_manager.transcribe_audio(audio, self.sample_rate, authorization)
                transcribe_time = int((time.time() - start_time) * 1000)

                if text:
                    self.stats['transcription_successes'] += 1
                    logger.success(f"✅ Remote transcribed ({transcribe_time}ms): \"{text}\"")
                    return text
                else:
                    logger.warning("⚠️ Remote transcription failed, falling back to local")
                    # Fall through to local transcription

            # Local transcription (fallback or if remote disabled)
            model = self._load_whisper_model()

            logger.info("📝 Transcribing audio with local Whisper...")
            start_time = time.time()

            # Whisper expects float32 audio
            result = model.transcribe(audio, fp16=False)  # fp16=False for CPU

            text = result['text'].strip()
            transcribe_time = int((time.time() - start_time) * 1000)

            if text:
                self.stats['transcription_successes'] += 1
                logger.success(f"✅ Local transcribed ({transcribe_time}ms): \"{text}\"")
                return text
            else:
                logger.warning("⚠️ Empty transcription")
                self.stats['transcription_failures'] += 1
                return None

        except Exception as e:
            logger.error(f"❌ Transcription failed: {e}")
            self.stats['transcription_failures'] += 1
            return None

    def _pitch_shift_audio(self, audio: np.ndarray, semitones: float, sample_rate: int) -> np.ndarray:
        """
        Shift pitch of audio by semitones using resampling

        Args:
            audio: Audio array (float32)
            semitones: Semitones to shift (-12 to +12, 0 = no change)
            sample_rate: Sample rate of audio

        Returns:
            Pitch-shifted audio array
        """
        if semitones == 0:
            return audio

        # Calculate pitch shift factor (2^(semitones/12))
        shift_factor = 2 ** (semitones / 12.0)

        # Resample audio to shift pitch
        # Higher shift_factor = higher pitch (faster playback)
        num_samples = int(len(audio) / shift_factor)

        # Use scipy's resample for high-quality pitch shifting
        shifted_audio = signal.resample(audio, num_samples)

        return shifted_audio

    def _clean_text_for_tts(self, text: str) -> str:
        """
        Clean text for TTS by removing/replacing punctuation that sounds bad when read aloud

        Args:
            text: Original text

        Returns:
            Cleaned text suitable for TTS
        """
        import re

        # Remove URLs (they sound terrible when read)
        text = re.sub(r'http[s]?://\S+', '', text)

        # Replace common punctuation with pauses
        text = text.replace('...', '. ')  # Ellipsis to period
        text = text.replace('…', '. ')    # Unicode ellipsis

        # Remove quotes (TTS doesn't need to say "quote")
        text = text.replace('"', '')
        text = text.replace('"', '')
        text = text.replace('"', '')
        text = text.replace("'", '')
        text = text.replace("'", '')
        text = text.replace("'", '')

        # Replace dashes with pauses
        text = text.replace(' - ', ', ')
        text = text.replace(' — ', ', ')
        text = text.replace(' – ', ', ')

        # Remove parentheses (keep content, remove parens)
        text = text.replace('(', '')
        text = text.replace(')', '')
        text = text.replace('[', '')
        text = text.replace(']', '')

        # Remove asterisks (markdown emphasis)
        text = text.replace('*', '')

        # Remove underscores (markdown emphasis)
        text = text.replace('_', ' ')

        # Replace semicolons with commas (more natural pause)
        text = text.replace(';', ',')

        # Remove colons that aren't part of time (e.g., "Note: " becomes "Note. ")
        text = re.sub(r':\s', '. ', text)

        # Clean up multiple spaces
        text = re.sub(r'\s+', ' ', text)

        # Clean up multiple punctuation
        text = re.sub(r'\.{2,}', '.', text)  # Multiple periods to single
        text = re.sub(r',{2,}', ',', text)   # Multiple commas to single

        return text.strip()

    def speak(self, text: str, emotion: Optional[str] = None) -> bool:
        """
        Speak text using TTS (Piper or pyttsx3) with mouth animation and emotion-based voice modulation

        Args:
            text: Text to speak
            emotion: Emotion state for voice modulation (e.g., 'happy', 'sarcasm', 'frustrated')
                    If None, uses default voice parameters

        Returns:
            True if successful, False otherwise
        """
        try:
            self._init_tts_engine()

            # Get emotion-based voice parameters (v2.1 - voice modulation)
            speed_multiplier = 1.0
            volume_multiplier = 1.0
            pitch_shift = 0
            emotion_label = ""

            if emotion and self.voice_emotions:
                emotion_params = self.voice_emotions.get(emotion)
                if emotion_params:
                    speed_multiplier = emotion_params.get('speed', 1.0)
                    volume_multiplier = emotion_params.get('volume', 1.0)
                    pitch_shift = emotion_params.get('pitch_shift', 0)
                    emotion_label = f" [{emotion}: speed={speed_multiplier:.2f}x, vol={volume_multiplier:.2f}x, pitch={pitch_shift:+d}st]"
                    logger.debug(f"Applying emotion '{emotion}': speed={speed_multiplier}, volume={volume_multiplier}, pitch_shift={pitch_shift}")
                else:
                    logger.warning(f"⚠️ Unknown emotion '{emotion}', using default voice")
            elif emotion:
                logger.debug(f"Emotion '{emotion}' provided but no voice_emotions loaded, using default voice")

            # Clean text for TTS (remove punctuation that sounds bad)
            cleaned_text = self._clean_text_for_tts(text)

            logger.info(f"🔊 Speaking{emotion_label}: \"{cleaned_text[:50]}{'...' if len(cleaned_text) > 50 else ''}\"")
            start_time = time.time()

            # Save current expression and switch to 'speaking' for proper eye positioning
            previous_expression = None
            if self.expression_engine:
                previous_expression = self.expression_engine.current_expression
                # Set to 'speaking' expression (eyelids: 60°) for natural talking appearance
                self.expression_engine.set_expression('speaking')
                logger.debug(f"Switched from '{previous_expression}' to 'speaking' expression for TTS")

            # Get servo controller for mouth animation (start later, after TTS synthesis)
            servo_controller = None
            mouth_animation_params = None
            if self.expression_engine and hasattr(self.expression_engine, 'servo_controller'):
                servo_controller = self.expression_engine.servo_controller
                if servo_controller:
                    # Get sensitivity from speaking expression (default 0.7)
                    speaking_expr = self.expression_engine.expressions.get('speaking', {})
                    mouth_config = speaking_expr.get('mouth', {})
                    mouth_animation_params = {
                        'sensitivity': mouth_config.get('sensitivity', 0.7),
                        'max_angle': mouth_config.get('max_angle', 50)
                    }

            try:
                if self.tts_engine == 'piper' and self.piper_voice:
                    # Use Piper TTS
                    audio_bytes = bytearray()
                    for chunk in self.piper_voice.synthesize(cleaned_text):
                        audio_bytes.extend(chunk.audio_int16_bytes)

                    # Convert to float32 audio
                    audio_array = np.frombuffer(bytes(audio_bytes), dtype=np.int16)
                    audio_float = audio_array.astype(np.float32) / 32767.0

                    # Apply emotion-based pitch shifting (v2.1)
                    original_sample_rate = self.piper_voice.config.sample_rate
                    if pitch_shift != 0:
                        logger.debug(f"Applying pitch shift: {pitch_shift:+d} semitones")
                        audio_float = self._pitch_shift_audio(audio_float, pitch_shift, original_sample_rate)

                    # Calculate playback sample rate for speed modulation (v2.1)
                    # Higher sample rate = faster playback
                    playback_sample_rate = int(original_sample_rate * speed_multiplier)
                    logger.debug(f"Playback speed: {speed_multiplier:.2f}x ({original_sample_rate}Hz -> {playback_sample_rate}Hz)")

                    # Audio-reactive mouth movement: analyze amplitude in real-time
                    if servo_controller and mouth_animation_params:
                        logger.info(f"🗣️ Starting AUDIO-REACTIVE mouth animation (sensitivity={mouth_animation_params['sensitivity']}, max_angle={mouth_animation_params['max_angle']})")

                        # Setup for audio-reactive animation
                        # Note: use playback_sample_rate for speed modulation
                        blocksize = int(playback_sample_rate * 0.03)  # 30ms chunks (faster = more responsive lip sync)
                        neutral = servo_controller.mouth_config['neutral_angle']
                        max_angle = mouth_animation_params['max_angle']
                        sensitivity = mouth_animation_params['sensitivity']
                        mouth_range = (max_angle - neutral) * sensitivity

                        # Cancel pending detach timers
                        if servo_controller._detach_timer:
                            servo_controller._detach_timer.cancel()

                        # Attach all servos (mouth for animation, eyes for natural blinking)
                        servo_controller.mouth.value = servo_controller.angle_to_servo_value_mouth(neutral)
                        servo_controller.current_mouth = neutral

                        # Keep eyes attached for natural blinking during speech
                        # Use current emotion angles from expression
                        logger.info(f"👁️ Setting eyelids for speech: left={servo_controller.current_left}°, right={servo_controller.current_right}°")
                        servo_controller.left_eyelid.value = servo_controller.angle_to_servo_value_left_eye(servo_controller.current_left)
                        servo_controller.right_eyelid.value = servo_controller.angle_to_servo_value_right_eye(servo_controller.current_right)

                        # Smoothing state (mutable list so callback can modify)
                        smoothed_amplitude = [0.0]  # Exponential moving average

                        # Eye blinking state for natural animation during speech
                        frame_count = [0]
                        last_blink_frame = [0]
                        blink_interval = int(playback_sample_rate * 4.0 / blocksize)  # Blink every ~4 seconds

                        # Audio-reactive callback: called for each audio chunk during playback
                        def audio_callback(outdata, frames, time_info, status):
                            """
                            Real-time audio callback - moves mouth based on actual audio amplitude
                            With faster EMA smoothing and natural eye blinks
                            """
                            # Calculate RMS amplitude of this audio chunk
                            rms = np.sqrt(np.mean(outdata**2))

                            # Apply non-linear scaling for more natural look
                            scaled_amplitude = np.sqrt(rms) * sensitivity * 8.0  # 8.0x boost for more dramatic movement

                            # Exponential moving average for smoothing (reduces jitter)
                            # alpha = 0.6 means 60% new value, 40% previous (faster response, less lag)
                            alpha = 0.6
                            smoothed_amplitude[0] = alpha * scaled_amplitude + (1 - alpha) * smoothed_amplitude[0]

                            # Clamp to 0-1
                            smoothed = min(1.0, max(0.0, smoothed_amplitude[0]))

                            # Calculate mouth position (no minimum threshold for maximum responsiveness)
                            mouth_pos = neutral + int(mouth_range * smoothed)
                            mouth_pos = max(neutral, min(max_angle, mouth_pos))

                            # Update mouth position (removed 1° threshold for faster response)
                            try:
                                servo_controller.mouth.value = servo_controller.angle_to_servo_value_mouth(mouth_pos)
                                servo_controller.current_mouth = mouth_pos
                            except:
                                pass  # Ignore errors in callback (don't crash audio playback)

                            # Natural eye blinks during speech
                            frame_count[0] += 1

                            # Check if it's time to start a new blink
                            if frame_count[0] - last_blink_frame[0] > blink_interval:
                                # Add variation to blink timing (±20%)
                                if random.random() < 0.1:  # 10% chance per check = natural variation
                                    try:
                                        # Quick blink both eyes
                                        servo_controller.left_eyelid.value = servo_controller.angle_to_servo_value_left_eye(0)
                                        servo_controller.right_eyelid.value = servo_controller.angle_to_servo_value_right_eye(0)
                                        last_blink_frame[0] = frame_count[0]
                                    except:
                                        pass

                            # Re-open eyes after brief pause (separate check)
                            elif frame_count[0] - last_blink_frame[0] == 3:  # 3 frames ≈ 90ms blink
                                try:
                                    servo_controller.left_eyelid.value = servo_controller.angle_to_servo_value_left_eye(servo_controller.current_left)
                                    servo_controller.right_eyelid.value = servo_controller.angle_to_servo_value_right_eye(servo_controller.current_right)
                                except:
                                    pass

                        # Play audio with real-time mouth animation using OutputStream
                        # Apply volume modulation (base volume * emotion volume multiplier)
                        audio_data = audio_float * self.tts_volume * volume_multiplier
                        frame_index = [0]  # Mutable counter for callback

                        def stream_callback(outdata, frames, time_info, status):
                            """Stream callback that plays audio AND animates mouth"""
                            start_idx = frame_index[0]
                            end_idx = start_idx + frames

                            if end_idx > len(audio_data):
                                # End of audio - pad with zeros
                                remaining = len(audio_data) - start_idx
                                if remaining > 0:
                                    outdata[:remaining, 0] = audio_data[start_idx:]
                                    outdata[remaining:, 0] = 0
                                else:
                                    outdata[:, 0] = 0
                                frame_index[0] = len(audio_data)
                            else:
                                # Normal playback
                                outdata[:, 0] = audio_data[start_idx:end_idx]
                                frame_index[0] = end_idx

                            # Call audio-reactive mouth animation
                            audio_callback(outdata, frames, time_info, status)

                        # Play audio with mouth animation (using modulated sample rate for speed control)
                        with sd.OutputStream(samplerate=playback_sample_rate, blocksize=blocksize,
                                           channels=1, callback=stream_callback):
                            # Wait for all audio to play
                            while frame_index[0] < len(audio_data):
                                sd.sleep(100)  # Sleep 100ms between checks

                        # Return mouth to neutral after speech
                        servo_controller.set_mouth(neutral, smooth=True, duration=0.2)
                    else:
                        # No servo controller - just play audio with emotion modulation
                        sd.play(audio_float * self.tts_volume * volume_multiplier, samplerate=playback_sample_rate)
                        sd.wait()
                else:
                    # Use pyttsx3
                    # Apply emotion modulation for pyttsx3 (speed and volume only, no pitch shift)
                    self.tts_engine.setProperty('rate', int(150 * self.tts_speed * speed_multiplier))
                    self.tts_engine.setProperty('volume', self.tts_volume * volume_multiplier)

                    # Start mouth animation right before pyttsx3 playback
                    if servo_controller and mouth_animation_params:
                        logger.info(f"🗣️ Starting mouth animation (sensitivity={mouth_animation_params['sensitivity']}, max_angle={mouth_animation_params['max_angle']})")
                        servo_controller.start_speech_animation(
                            base_amplitude=mouth_animation_params['sensitivity'],
                            max_angle_override=mouth_animation_params['max_angle']
                        )

                    self.tts_engine.say(cleaned_text)
                    self.tts_engine.runAndWait()

                    # Return mouth to neutral after pyttsx3 speech
                    if servo_controller:
                        servo_controller.set_mouth(servo_controller.mouth_config['neutral_angle'], smooth=True, duration=0.2)
            finally:
                # Restore previous expression after speaking
                if self.expression_engine and previous_expression:
                    self.expression_engine.set_expression(previous_expression)
                    logger.debug(f"Restored expression to '{previous_expression}' after speech")
                # Ensure servos detach after idle period (handled by idle timer in servo_controller)

            speak_time = int((time.time() - start_time) * 1000)
            self.stats['tts_successes'] += 1
            logger.success(f"✅ Spoke text ({speak_time}ms)")
            return True

        except Exception as e:
            logger.error(f"❌ TTS failed: {e}")
            self.stats['tts_failures'] += 1
            return False

    def process_voice_query(self, use_vad: bool = True, duration: float = 3.0, authorization: Optional[Dict] = None, expression: str = 'listening') -> Optional[str]:
        """
        Complete voice interaction: record → process (transcribe + query) → speak

        OPTIMIZED: Single call to Gary for transcription + LLM processing

        Args:
            use_vad: Use Voice Activity Detection (auto-stop when done speaking)
            duration: Recording duration in seconds (only used if use_vad=False)
            authorization: Authorization context for LLM query
            expression: Current expression state (for display)

        Returns:
            Response text or None if failed
        """
        start_time = time.time()

        # Update expression: listening state
        if self.expression_engine:
            try:
                self.expression_engine.set_expression('listening')
            except Exception as e:
                logger.debug(f"Expression engine not available: {e}")

        # Update display: listening state
        if self.arduino_display and self.arduino_display.connected:
            self.arduino_display.update_status(
                state="listening",
                expression="listening"
            )

        # Step 1: Record audio (with VAD or fixed duration)
        # Use VAD if enabled in config (unless explicitly overridden)
        use_vad_final = use_vad and self.vad_enabled

        if use_vad_final:
            audio = self.record_audio_with_vad(
                max_duration=self.vad_max_duration,
                silence_duration=self.vad_silence_duration,
                vad_aggressiveness=self.vad_aggressiveness
            )
        else:
            audio = self.record_audio(duration)

        if audio is None:
            logger.error("Voice query failed: No audio recorded")
            if self.expression_engine:
                try:
                    self.expression_engine.set_expression('confused')
                except:
                    pass
            return None

        # Step 2: Process audio (transcribe + query in ONE call) - OPTIMIZED
        if self.llm_manager is None:
            logger.warning("No LLM manager configured, cannot process audio")
            return None

        # Update expression: thinking
        if self.expression_engine:
            try:
                self.expression_engine.set_expression('thinking')
            except:
                pass

        logger.info("🤖 Processing audio query via Gary (full pipeline)...")
        try:
            # NEW: Single call for transcription + LLM processing
            result = self.llm_manager.process_audio_query(audio, self.sample_rate, authorization)

            if not result or not result.get('response'):
                logger.error("❌ Audio processing returned no response")
                if self.expression_engine:
                    try:
                        self.expression_engine.set_expression('confused')
                    except:
                        pass
                return None

            transcription = result.get('transcription', '')
            response_text = result['response']
            tier = result.get('tier', 'unknown')
            model = result.get('model', 'unknown')

            # Get emotion from Gary's response (v2.1) - handle list or string
            emotion_data = result.get('emotion', 'idle')
            if isinstance(emotion_data, list) and len(emotion_data) > 0:
                current_emotion = emotion_data[0]  # Use primary emotion
                logger.debug(f"Multiple emotions received: {emotion_data}, using primary: {current_emotion}")
            else:
                current_emotion = emotion_data if isinstance(emotion_data, str) else 'idle'

            logger.success(f"✅ Got response from {tier} tier (model: {model})")
            logger.info(f"   Transcribed: \"{transcription}\"")

        except Exception as e:
            logger.error(f"❌ Audio processing failed: {e}")
            if self.expression_engine:
                try:
                    self.expression_engine.set_expression('error')
                except:
                    pass
            return None

        # Calculate response time
        response_time = time.time() - start_time

        # Update display: show conversation
        if self.arduino_display and self.arduino_display.connected:
            self.arduino_display.show_conversation(
                user_text=transcription,
                gairi_text=response_text,
                expression=current_emotion,  # Use Gary's emotion (v2.1)
                tier=tier,
                response_time=response_time
            )

            # Also update debug page data (PAGE 3)
            self.arduino_display.show_debug(
                tier=tier,
                tool="voice_pipeline",
                training_logged=True,  # Gary server handles training
                response_time=response_time
            )

        # Step 3: Speak response with emotion-based voice modulation (v2.1)
        # Set visual expression to match Gary's emotion
        if result.get('emotion') and self.expression_engine:
            try:
                self.expression_engine.set_expression(result['emotion'])
                logger.info(f"🎭 Expression & Voice: {current_emotion}")
            except:
                pass

        # Speak with emotion-based voice modulation
        # NOTE: Don't set to 'speaking' - let emotion expression show during speech
        self.speak(response_text, emotion=current_emotion)

        # Update stats
        total_time = int((time.time() - start_time) * 1000)
        self.stats['total_processing_time_ms'] += total_time
        logger.info(f"🏁 Voice interaction complete ({total_time}ms)")

        return response_text

    def test_pipeline(self) -> bool:
        """
        Test complete voice pipeline

        Returns:
            True if all components work, False otherwise
        """
        logger.info("=" * 60)
        logger.info("Testing Voice Pipeline")
        logger.info("=" * 60)

        # Test 1: TTS
        logger.info("\n1. Testing TTS...")
        if not self.speak("Testing text to speech"):
            logger.error("❌ TTS test failed")
            return False

        # Test 2: Microphone
        logger.info("\n2. Testing microphone (3 seconds)...")
        logger.info("   Speak now or make noise...")
        audio = self.record_audio(duration=3.0)
        if audio is None:
            logger.error("❌ Microphone test failed")
            return False

        # Test 3: Whisper transcription
        logger.info("\n3. Testing Whisper transcription...")
        text = self.transcribe_audio(audio)
        if text is None:
            logger.warning("⚠️ No speech detected (silence or unclear audio)")
        else:
            logger.success(f"✅ Transcribed: \"{text}\"")

        # Test 4: Full pipeline (if LLM manager available)
        if self.llm_manager:
            logger.info("\n4. Testing full pipeline...")
            logger.info("   Say something for 3 seconds...")
            response = self.process_voice_query(duration=3.0)
            if response:
                logger.success(f"✅ Pipeline test complete: \"{response}\"")
            else:
                logger.warning("⚠️ Pipeline test failed")

        logger.info("\n" + "=" * 60)
        logger.info("Test Summary")
        logger.info("=" * 60)
        logger.info(f"TTS: ✅ Working")
        logger.info(f"Microphone: ✅ Working")
        logger.info(f"Whisper: {'✅ Working' if text else '⚠️ Silent/unclear'}")
        logger.info(f"LLM: {'✅ Available' if self.llm_manager else '❌ Not configured'}")

        return True

    def get_stats(self) -> Dict:
        """
        Get usage statistics

        Returns:
            Dict of statistics
        """
        stats = self.stats.copy()

        if stats['total_recordings'] > 0:
            stats['transcription_success_rate'] = (
                stats['transcription_successes'] / stats['total_recordings'] * 100
            )
            stats['avg_processing_time_ms'] = (
                stats['total_processing_time_ms'] / stats['total_recordings']
            )
        else:
            stats['transcription_success_rate'] = 0
            stats['avg_processing_time_ms'] = 0

        return stats


# Test harness
if __name__ == '__main__':
    import yaml
    import sys
    from loguru import logger

    # Configure logging
    logger.remove()
    logger.add(sys.stderr, level="DEBUG")

    print("VoiceHandler Test")
    print("=" * 60)

    # Load config
    config_path = Path(__file__).parent.parent / 'config' / 'gairi_head.yaml'
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    # Initialize voice handler
    handler = VoiceHandler(config)

    # Run pipeline test
    handler.test_pipeline()

    # Show stats
    print("\n" + "=" * 60)
    print("Statistics:")
    stats = handler.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    print("\n✅ VoiceHandler test complete")
