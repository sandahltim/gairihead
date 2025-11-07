#!/usr/bin/env python3
"""
GairiHead Voice Assistant - Main Application

Version: 1.0 (2025-11-07)
Purpose: Complete voice assistant with face recognition authorization

Flow:
1. Initialize components (camera, voice, LLM, face recognition)
2. Wait for interaction trigger (button press or face detection)
3. Capture face → Determine authorization level
4. Listen to voice query
5. Process through Gary (with authorization context)
6. Speak response
7. Log training data (server-side)

Core Principles Applied:
- #6: Trust but verify (test each component before integration)
- #8: Do it well (proper error handling, simple first)
"""

import asyncio
import signal
import sys
import time
from pathlib import Path
from datetime import datetime
from loguru import logger
import yaml

# Import GairiHead components
from src.voice_handler import VoiceHandler
from src.llm_tier_manager import LLMTierManager
from src.camera_manager import CameraManager
from src.vision_handler import VisionHandler
from src.arduino_display import ArduinoDisplay


class GairiHeadAssistant:
    """Main voice assistant application"""
    
    def __init__(self, config_path: Path):
        """
        Initialize GairiHead assistant
        
        Args:
            config_path: Path to gairi_head.yaml config file
        """
        # Load config
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        logger.info("=== GairiHead Voice Assistant v1.0 ===")
        
        # Initialize components
        self.camera = None
        self.vision = None
        self.llm_manager = None
        self.arduino_display = None
        self.voice = None
        
        # State
        self.running = False
        self.interaction_count = 0
        
    async def initialize(self) -> bool:
        """
        Initialize all components
        
        Returns:
            True if all critical components initialized, False otherwise
        """
        logger.info("Initializing components...")
        
        # 1. Camera Manager
        try:
            logger.info("1. Initializing camera...")
            # CameraManager expects config_path, not config dict
            # Pass None to use default config path
            self.camera = CameraManager(config_path=None)
            if self.camera.initialize():
                logger.success("✅ Camera initialized")
            else:
                logger.warning("⚠️ Camera failed to initialize (continuing without face recognition)")
        except Exception as e:
            logger.error(f"❌ Camera initialization failed: {e}")
            self.camera = None
        
        # 2. Vision Handler (face recognition)
        try:
            logger.info("2. Initializing face recognition...")
            self.vision = VisionHandler(self.config)
            logger.success("✅ Face recognition initialized")
        except Exception as e:
            logger.error(f"❌ Face recognition initialization failed: {e}")
            self.vision = None
        
        # 3. LLM Tier Manager (REQUIRED)
        try:
            logger.info("3. Initializing LLM tier manager...")
            self.llm_manager = LLMTierManager(self.config)
            logger.success("✅ LLM manager initialized")
        except Exception as e:
            logger.error(f"❌ LLM manager initialization FAILED: {e}")
            logger.error("Cannot continue without LLM manager")
            return False

        # 4. Arduino Display (OPTIONAL)
        try:
            logger.info("4. Initializing Arduino display...")
            display_config = self.config.get('arduino_display', {})
            enabled = display_config.get('enabled', False)

            if enabled:
                self.arduino_display = ArduinoDisplay(
                    port=display_config.get('port', '/dev/ttyACM0'),
                    baudrate=display_config.get('baudrate', 115200),
                    enabled=True
                )
                if self.arduino_display.connected:
                    logger.success("✅ Arduino display connected")
                else:
                    logger.warning("⚠️ Arduino display configured but not connected")
                    self.arduino_display = None
            else:
                logger.info("   Arduino display disabled in config")
        except Exception as e:
            logger.error(f"❌ Arduino display initialization failed: {e}")
            self.arduino_display = None

        # 5. Voice Handler (REQUIRED)
        try:
            logger.info("5. Initializing voice handler...")
            self.voice = VoiceHandler(
                self.config,
                llm_tier_manager=self.llm_manager,
                arduino_display=self.arduino_display
            )
            logger.success("✅ Voice handler initialized")
        except Exception as e:
            logger.error(f"❌ Voice handler initialization FAILED: {e}")
            logger.error("Cannot continue without voice handler")
            return False
        
        logger.info("=" * 60)
        logger.success("✅ GairiHead initialized successfully")
        logger.info("=" * 60)
        
        return True
    
    def get_authorization(self) -> dict:
        """
        Determine authorization level through face recognition
        
        Returns:
            Authorization dict with level, user, confidence
        """
        # If camera/vision not available, default to stranger mode
        if self.camera is None or self.vision is None:
            logger.warning("No face recognition - defaulting to stranger mode")
            return {
                'level': 3,
                'user': 'unknown',
                'confidence': 0.0
            }
        
        try:
            # Capture frame
            frame = self.camera.capture_frame()
            if frame is None:
                logger.warning("Failed to capture frame - defaulting to stranger mode")
                return {
                    'level': 3,
                    'user': 'unknown',
                    'confidence': 0.0
                }
            
            # Recognize face
            result = self.vision.recognize_face(frame)
            
            if result['recognized']:
                logger.info(f"🎯 Recognized: {result['name']} (confidence: {result['confidence']:.2f})")
                
                # Map name to authorization level
                # Level 1: Main users (Tim)
                # Level 2: Guests (registered but limited access)
                # Level 3: Strangers (unknown faces)
                
                if result['name'].lower() == 'tim':
                    level = 1
                elif result['name'].lower() in ['guest1', 'guest2']:  # Example guest names
                    level = 2
                else:
                    level = 3
                
                return {
                    'level': level,
                    'user': result['name'],
                    'confidence': result['confidence']
                }
            else:
                logger.info("👤 Unknown face detected - stranger mode")
                return {
                    'level': 3,
                    'user': 'unknown',
                    'confidence': 0.0
                }
        
        except Exception as e:
            logger.error(f"Face recognition error: {e}")
            return {
                'level': 3,
                'user': 'unknown',
                'confidence': 0.0
            }
    
    async def handle_interaction(self):
        """Handle a single voice interaction"""
        self.interaction_count += 1
        
        logger.info(f"\n{'=' * 60}")
        logger.info(f"Interaction #{self.interaction_count}")
        logger.info(f"{'=' * 60}")
        
        # Step 1: Get authorization through face recognition
        logger.info("Step 1: Checking authorization...")
        authorization = self.get_authorization()
        
        auth_level_name = {1: 'Main User', 2: 'Guest', 3: 'Stranger'}
        logger.info(f"Authorization: Level {authorization['level']} ({auth_level_name[authorization['level']]})")
        
        # Step 2: Listen to voice query
        logger.info("Step 2: Listening for voice query (3 seconds)...")
        logger.info("🎤 Speak now...")
        
        try:
            # Process voice query (record → transcribe → query Gary → speak)
            response = self.voice.process_voice_query(
                duration=3.0,
                authorization=authorization
            )
            
            if response:
                logger.success(f"✅ Interaction complete")
            else:
                logger.warning("⚠️ Interaction failed")
        
        except Exception as e:
            logger.error(f"❌ Interaction error: {e}")
    
    async def run_interactive_mode(self):
        """
        Run in interactive mode (press Enter to trigger interaction)
        
        This is the simple "do it well" mode - button triggered instead of
        continuous listening with wake words (Core Principle #8)
        """
        logger.info("\n" + "=" * 60)
        logger.info("GairiHead Voice Assistant - Interactive Mode")
        logger.info("=" * 60)
        logger.info("Press ENTER to trigger voice interaction")
        logger.info("Press Ctrl+C to exit")
        logger.info("=" * 60 + "\n")
        
        self.running = True
        
        try:
            while self.running:
                # Wait for Enter key
                await asyncio.get_event_loop().run_in_executor(
                    None, input, "\nPress ENTER to start interaction... "
                )
                
                # Handle interaction
                await self.handle_interaction()
        
        except KeyboardInterrupt:
            logger.info("\n\nShutting down...")
            self.running = False
    
    async def run_continuous_mode(self, interval: float = 5.0):
        """
        Run in continuous mode (auto-trigger at intervals for testing)
        
        Args:
            interval: Seconds between interactions
        """
        logger.info("\n" + "=" * 60)
        logger.info("GairiHead Voice Assistant - Continuous Mode")
        logger.info("=" * 60)
        logger.info(f"Auto-triggering every {interval} seconds")
        logger.info("Press Ctrl+C to exit")
        logger.info("=" * 60 + "\n")
        
        self.running = True
        
        try:
            while self.running:
                await self.handle_interaction()
                
                # Wait before next interaction
                logger.info(f"Waiting {interval} seconds before next interaction...")
                await asyncio.sleep(interval)
        
        except KeyboardInterrupt:
            logger.info("\n\nShutting down...")
            self.running = False
    
    def get_stats(self) -> dict:
        """Get usage statistics"""
        stats = {
            'total_interactions': self.interaction_count,
            'voice_stats': self.voice.get_stats() if self.voice else {},
            'components': {
                'camera': self.camera is not None,
                'vision': self.vision is not None,
                'llm': self.llm_manager is not None,
                'voice': self.voice is not None
            }
        }
        return stats
    
    def shutdown(self):
        """Clean shutdown of all components"""
        logger.info("Shutting down GairiHead...")
        
        if self.camera:
            self.camera.release()
        
        logger.info("✅ Shutdown complete")


async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="GairiHead Voice Assistant")
    parser.add_argument(
        '--mode',
        choices=['interactive', 'continuous', 'test'],
        default='interactive',
        help='Run mode: interactive (button), continuous (auto), or test (component tests)'
    )
    parser.add_argument(
        '--interval',
        type=float,
        default=5.0,
        help='Interval for continuous mode (seconds)'
    )
    parser.add_argument(
        '--config',
        type=str,
        default='config/gairi_head.yaml',
        help='Config file path'
    )
    
    args = parser.parse_args()
    
    # Configure logging
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    logger.add(
        "logs/gairi_head_{time:YYYY-MM-DD}.log",
        rotation="1 day",
        retention="30 days",
        level="DEBUG"
    )
    
    # Initialize assistant
    config_path = Path(__file__).parent / args.config
    assistant = GairiHeadAssistant(config_path)
    
    if not await assistant.initialize():
        logger.error("Failed to initialize GairiHead - exiting")
        return 1
    
    # Run based on mode
    try:
        if args.mode == 'test':
            logger.info("Running component tests...")
            
            # Test voice pipeline
            logger.info("\n=== Testing Voice Pipeline ===")
            assistant.voice.test_pipeline()
            
            # Show stats
            logger.info("\n=== Statistics ===")
            stats = assistant.get_stats()
            for key, value in stats.items():
                logger.info(f"{key}: {value}")
        
        elif args.mode == 'continuous':
            await assistant.run_continuous_mode(interval=args.interval)
        
        else:  # interactive
            await assistant.run_interactive_mode()
    
    finally:
        assistant.shutdown()
        
        # Show final stats
        logger.info("\n=== Final Statistics ===")
        stats = assistant.get_stats()
        logger.info(f"Total interactions: {stats['total_interactions']}")
        if stats['voice_stats']:
            for key, value in stats['voice_stats'].items():
                logger.info(f"  {key}: {value}")
    
    return 0


if __name__ == '__main__':
    sys.exit(asyncio.run(main()))
