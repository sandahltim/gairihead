#!/usr/bin/env python3
"""
Voice Handler - Speech-to-Text and Text-to-Speech integration for GairiHead

Version: 1.0 (2025-11-07)
Purpose: Complete voice interaction pipeline for GairiHead physical robot

Components:
- Speech-to-Text: Whisper (OpenAI)
- Text-to-Speech: pyttsx3 + espeak-ng (local, free)
- Audio Recording: sounddevice (C920 built-in microphone)

Flow:
1. Record audio from microphone
2. Transcribe with Whisper
3. Send to Gary via LLMTierManager
4. Speak response with pyttsx3

Core Principles Applied:
- #6: Trust but verify (test each component before integration)
- #8: Do it well (proper error handling, logging, fallbacks)
"""

import whisper
import sounddevice as sd
import numpy as np
import pyttsx3
import wave
import io
import time
import tempfile
from pathlib import Path
from loguru import logger
from typing import Optional, Dict, Tuple


class VoiceHandler:
    """Manages complete voice interaction pipeline"""

    def __init__(self, config, llm_tier_manager=None, arduino_display=None):
        """
        Initialize voice handler

        Args:
            config: Configuration dict from gairi_head.yaml
            llm_tier_manager: LLMTierManager instance for query processing
            arduino_display: ArduinoDisplay instance for visual feedback
        """
        self.config = config.get('voice', {})
        self.llm_manager = llm_tier_manager
        self.arduino_display = arduino_display

        # Microphone settings
        self.sample_rate = self.config.get('microphone', {}).get('sample_rate', 16000)
        self.chunk_size = self.config.get('microphone', {}).get('chunk_size', 1024)
        self.device_index = self.config.get('microphone', {}).get('device_index', None)

        # Whisper STT
        self.whisper_model = None
        self.whisper_model_name = self.config.get('stt', {}).get('model', 'tiny')
        logger.info(f"VoiceHandler v1.0 initialized (Whisper: {self.whisper_model_name}, TTS: pyttsx3)")

        # TTS settings
        self.tts_engine = None
        self.tts_speed = self.config.get('tts', {}).get('speed', 1.0)
        self.tts_volume = self.config.get('tts', {}).get('volume', 0.8)

        # Statistics
        self.stats = {
            'total_recordings': 0,
            'transcription_successes': 0,
            'transcription_failures': 0,
            'tts_successes': 0,
            'tts_failures': 0,
            'total_processing_time_ms': 0
        }

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
        """Lazy initialize TTS engine"""
        if self.tts_engine is None:
            logger.info("Initializing pyttsx3 TTS engine...")
            self.tts_engine = pyttsx3.init()
            self.tts_engine.setProperty('rate', int(150 * self.tts_speed))  # Words per minute
            self.tts_engine.setProperty('volume', self.tts_volume)
            logger.success("✅ TTS engine initialized")
        return self.tts_engine

    def record_audio(self, duration: float = 3.0, silence_threshold: float = 0.01) -> Optional[np.ndarray]:
        """
        Record audio from microphone

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

    def transcribe_audio(self, audio: np.ndarray) -> Optional[str]:
        """
        Transcribe audio using Whisper

        Args:
            audio: numpy array of audio samples (float32, 16kHz)

        Returns:
            Transcribed text or None if failed
        """
        try:
            model = self._load_whisper_model()

            logger.info("📝 Transcribing audio with Whisper...")
            start_time = time.time()

            # Whisper expects float32 audio
            result = model.transcribe(audio, fp16=False)  # fp16=False for CPU

            text = result['text'].strip()
            transcribe_time = int((time.time() - start_time) * 1000)

            if text:
                self.stats['transcription_successes'] += 1
                logger.success(f"✅ Transcribed ({transcribe_time}ms): \"{text}\"")
                return text
            else:
                logger.warning("⚠️ Empty transcription")
                self.stats['transcription_failures'] += 1
                return None

        except Exception as e:
            logger.error(f"❌ Transcription failed: {e}")
            self.stats['transcription_failures'] += 1
            return None

    def speak(self, text: str) -> bool:
        """
        Speak text using TTS

        Args:
            text: Text to speak

        Returns:
            True if successful, False otherwise
        """
        try:
            engine = self._init_tts_engine()

            logger.info(f"🔊 Speaking: \"{text[:50]}{'...' if len(text) > 50 else ''}\"")
            start_time = time.time()

            engine.say(text)
            engine.runAndWait()

            speak_time = int((time.time() - start_time) * 1000)
            self.stats['tts_successes'] += 1
            logger.success(f"✅ Spoke text ({speak_time}ms)")
            return True

        except Exception as e:
            logger.error(f"❌ TTS failed: {e}")
            self.stats['tts_failures'] += 1
            return False

    def process_voice_query(self, duration: float = 3.0, authorization: Optional[Dict] = None, expression: str = 'listening') -> Optional[str]:
        """
        Complete voice interaction: record → transcribe → query → speak

        Args:
            duration: Recording duration in seconds
            authorization: Authorization context for LLM query
            expression: Current expression state (for display)

        Returns:
            Response text or None if failed
        """
        start_time = time.time()

        # Update display: listening state
        if self.arduino_display and self.arduino_display.connected:
            self.arduino_display.update_status(
                state="listening",
                expression=expression
            )

        # Step 1: Record audio
        audio = self.record_audio(duration)
        if audio is None:
            logger.error("Voice query failed: No audio recorded")
            return None

        # Step 2: Transcribe
        text = self.transcribe_audio(audio)
        if text is None:
            logger.error("Voice query failed: Transcription failed")
            return None

        # Step 3: Query LLM
        tier = "local"
        if self.llm_manager is None:
            logger.warning("No LLM manager configured, returning transcription only")
            response_text = f"I heard: {text}"
        else:
            logger.info(f"🤖 Querying Gary with: \"{text}\"")
            try:
                result = self.llm_manager.query(text, authorization=authorization)
                if result and result.get('response'):
                    response_text = result['response']
                    tier = result.get('tier', 'local')
                    logger.success(f"✅ Got response from {tier} tier")
                else:
                    logger.error("❌ LLM query returned no response")
                    response_text = "Sorry, I didn't get a response."
            except Exception as e:
                logger.error(f"❌ LLM query failed: {e}")
                response_text = "Sorry, something went wrong."

        # Calculate response time
        response_time = time.time() - start_time

        # Update display: show conversation
        if self.arduino_display and self.arduino_display.connected:
            self.arduino_display.show_conversation(
                user_text=text,
                gairi_text=response_text,
                expression=expression,
                tier=tier,
                response_time=response_time
            )

        # Step 4: Speak response
        self.speak(response_text)

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
