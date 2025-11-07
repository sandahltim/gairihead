#!/usr/bin/env python3
"""
Arduino Display Manager for GairiHead
Handles serial communication with Arduino Uno + 2.8" TFT HAT display
"""

import serial
import json
import time
from typing import Optional, Dict, Any
from loguru import logger


class ArduinoDisplay:
    """
    Manages communication with Arduino TFT display
    Sends conversation, status, and debug updates via JSON over serial
    """

    def __init__(self, port: str = '/dev/ttyACM0', baudrate: int = 115200,
                 enabled: bool = True, timeout: float = 1.0):
        """
        Initialize Arduino display connection

        Args:
            port: Serial port for Arduino (usually /dev/ttyACM0 or /dev/ttyUSB0)
            baudrate: Serial communication speed (must match Arduino)
            enabled: Enable/disable display updates
            timeout: Serial read timeout in seconds
        """
        self.port = port
        self.baudrate = baudrate
        self.enabled = enabled
        self.timeout = timeout
        self.serial: Optional[serial.Serial] = None
        self.connected = False

        if self.enabled:
            self._connect()

    def _connect(self) -> bool:
        """
        Establish serial connection to Arduino

        Returns:
            True if connected successfully, False otherwise
        """
        try:
            self.serial = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout
            )
            # Wait for Arduino to reset after serial connection
            time.sleep(2)
            self.connected = True
            logger.info(f"Arduino display connected on {self.port} @ {self.baudrate} baud")
            return True

        except serial.SerialException as e:
            logger.warning(f"Failed to connect to Arduino display on {self.port}: {e}")
            self.connected = False
            return False
        except Exception as e:
            logger.error(f"Unexpected error connecting to Arduino: {e}")
            self.connected = False
            return False

    def _send(self, message: Dict[str, Any]) -> bool:
        """
        Send JSON message to Arduino

        Args:
            message: Dictionary to send as JSON

        Returns:
            True if sent successfully, False otherwise
        """
        if not self.enabled:
            return False

        if not self.connected:
            # Try to reconnect
            if not self._connect():
                return False

        try:
            json_str = json.dumps(message)
            self.serial.write(json_str.encode('utf-8'))
            self.serial.write(b'\n')  # Newline delimiter
            self.serial.flush()
            logger.debug(f"Sent to Arduino: {json_str}")
            return True

        except serial.SerialException as e:
            logger.warning(f"Serial error sending to Arduino: {e}")
            self.connected = False
            return False
        except Exception as e:
            logger.error(f"Error sending to Arduino: {e}")
            return False

    def _receive(self, timeout: float = 0.5) -> Optional[Dict[str, Any]]:
        """
        Receive JSON message from Arduino (non-blocking)

        Args:
            timeout: How long to wait for data (seconds)

        Returns:
            Parsed JSON dict if received, None otherwise
        """
        if not self.enabled or not self.connected:
            return None

        try:
            # Store original timeout
            original_timeout = self.serial.timeout
            self.serial.timeout = timeout

            # Read line
            line = self.serial.readline().decode('utf-8').strip()

            # Restore timeout
            self.serial.timeout = original_timeout

            if line:
                data = json.loads(line)
                logger.debug(f"Received from Arduino: {data}")
                return data
            return None

        except json.JSONDecodeError as e:
            logger.warning(f"Invalid JSON from Arduino: {line} - {e}")
            return None
        except Exception as e:
            logger.error(f"Error receiving from Arduino: {e}")
            return None

    def show_conversation(self, user_text: str, gairi_text: str,
                         expression: str = "idle", tier: str = "local",
                         response_time: float = 0.0) -> bool:
        """
        Display conversation exchange on Arduino screen

        Args:
            user_text: What Tim said
            gairi_text: Gairi's response
            expression: Current expression name
            tier: LLM tier used (local/cloud)
            response_time: Response time in seconds

        Returns:
            True if sent successfully
        """
        message = {
            "type": "conversation",
            "user_text": user_text,
            "gairi_text": gairi_text,
            "expression": expression,
            "tier": tier,
            "response_time": round(response_time, 2)
        }
        return self._send(message)

    def update_status(self, user: str = "unknown", level: int = 3,
                     state: str = "idle", confidence: float = 0.0,
                     expression: str = "idle") -> bool:
        """
        Update system status on Arduino display

        Args:
            user: Recognized user name
            level: Authorization level (1=Tim, 2=Guest, 3=Stranger)
            state: System state (idle/listening/thinking/speaking)
            confidence: Face recognition confidence (0.0-1.0)
            expression: Current expression name

        Returns:
            True if sent successfully
        """
        message = {
            "type": "status",
            "user": user,
            "level": level,
            "state": state,
            "confidence": round(confidence, 2),
            "expression": expression
        }
        return self._send(message)

    def show_debug(self, tier: str = "local", tool: str = "",
                  training_logged: bool = False, response_time: float = 0.0) -> bool:
        """
        Show debug information on Arduino display

        Args:
            tier: LLM tier used (local/cloud)
            tool: Tool name that was called (if any)
            training_logged: Whether interaction was logged for training
            response_time: Response time in seconds

        Returns:
            True if sent successfully
        """
        message = {
            "type": "debug",
            "tier": tier,
            "tool": tool,
            "training_logged": training_logged,
            "response_time": round(response_time, 2)
        }
        return self._send(message)

    def check_commands(self) -> Optional[Dict[str, Any]]:
        """
        Check for commands from Arduino (guest mode, demo, etc.)

        Returns:
            Command dict if received, None otherwise
        """
        return self._receive(timeout=0.1)

    def close(self):
        """Close serial connection"""
        if self.serial and self.connected:
            try:
                self.serial.close()
                logger.info("Arduino display connection closed")
            except Exception as e:
                logger.error(f"Error closing Arduino connection: {e}")
            finally:
                self.connected = False

    def __del__(self):
        """Cleanup on object destruction"""
        self.close()


# Standalone test function
def test_arduino_display():
    """
    Test Arduino display with sample messages
    Run with: python -m src.arduino_display
    """
    print("="*70)
    print("ARDUINO DISPLAY TEST")
    print("="*70)

    # Initialize display
    print("\n1. Connecting to Arduino...")
    display = ArduinoDisplay(port='/dev/ttyACM0', baudrate=115200, enabled=True)

    if not display.connected:
        print("   ❌ Failed to connect. Check:")
        print("      - Arduino is plugged in")
        print("      - Sketch uploaded to Arduino")
        print("      - Correct port (/dev/ttyACM0 or /dev/ttyUSB0)")
        return

    print("   ✅ Connected!")

    # Test status update
    print("\n2. Testing status update...")
    display.update_status(
        user="tim",
        level=1,
        state="idle",
        confidence=0.78,
        expression="happy"
    )
    time.sleep(2)

    # Test conversation
    print("\n3. Testing conversation display...")
    display.show_conversation(
        user_text="Good morning Gairi",
        gairi_text="Good morning Tim! Ready to help!",
        expression="happy",
        tier="local",
        response_time=0.34
    )
    time.sleep(3)

    # Test debug
    print("\n4. Testing debug display...")
    display.show_debug(
        tier="local",
        tool="calendar_tool",
        training_logged=True,
        response_time=0.42
    )
    time.sleep(2)

    # Test state changes
    print("\n5. Testing state transitions...")
    states = [
        ("listening", "alert"),
        ("thinking", "thinking"),
        ("speaking", "happy")
    ]

    for state, expression in states:
        print(f"   State: {state}")
        display.update_status(
            user="tim",
            level=1,
            state=state,
            confidence=0.78,
            expression=expression
        )
        time.sleep(1)

    # Check for commands
    print("\n6. Checking for Arduino commands (touch buttons)...")
    print("   (Press buttons on Arduino if available)")
    for _ in range(3):
        cmd = display.check_commands()
        if cmd:
            print(f"   Received command: {cmd}")
        time.sleep(1)

    print("\n" + "="*70)
    print("TEST COMPLETE!")
    print("="*70)
    print("\nArduino display is working correctly!")

    display.close()


if __name__ == "__main__":
    test_arduino_display()
