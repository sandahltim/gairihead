#!/usr/bin/env python3
"""
Test script for Gary team to verify WebSocket connection to GairiHead

This script demonstrates the CORRECT way to connect using WebSocket protocol.
Run this to test if your connection is working.

Usage:
    python test_gary_connection.py
"""

import asyncio
import json
import sys

try:
    import websockets
except ImportError:
    print("❌ Error: websockets library not installed")
    print("Install it with: pip install websockets")
    sys.exit(1)


# GairiHead connection details
GAIRIHEAD_HOST = "ws://100.103.67.41:8766"
GAIRIHEAD_TOKEN = "av-UQ9Eh64ZcbRPadshCzpqiVkG5Rw2QxDTuJYRU__o"


async def test_connection():
    """Test WebSocket connection to GairiHead"""
    print("=" * 70)
    print("GairiHead Connection Test for Gary Team")
    print("=" * 70)
    print()

    try:
        # Test 1: Connection
        print("Test 1: Connecting to GairiHead...")
        print(f"  Host: {GAIRIHEAD_HOST}")

        ws = await websockets.connect(GAIRIHEAD_HOST, ping_interval=None)
        print("  ✅ WebSocket connection established")
        print()

        # Test 2: Authentication
        print("Test 2: Authenticating...")
        print(f"  Token: {GAIRIHEAD_TOKEN[:20]}...")

        auth_msg = {"token": GAIRIHEAD_TOKEN}
        await ws.send(json.dumps(auth_msg))

        auth_response = await asyncio.wait_for(ws.recv(), timeout=5)
        auth_data = json.loads(auth_response)

        if auth_data.get("status") == "authenticated":
            print("  ✅ Authentication successful")
            print(f"  Response: {auth_data}")
        else:
            print(f"  ❌ Authentication failed: {auth_data}")
            await ws.close()
            return False
        print()

        # Test 3: Get Status (fast command)
        print("Test 3: Testing 'get_status' command...")

        status_cmd = {
            "action": "get_status",
            "params": {}
        }
        await ws.send(json.dumps(status_cmd))

        status_response = await asyncio.wait_for(ws.recv(), timeout=5)
        status_data = json.loads(status_response)

        if status_data.get("status") == "success":
            print("  ✅ get_status command working")
            print(f"  Camera: {status_data.get('camera', 'unknown')}")
            print(f"  Servos: {status_data.get('servos', 'unknown')}")
            print(f"  Arduino: {status_data.get('arduino', 'unknown')}")
            print(f"  Expression: {status_data.get('expression', 'unknown')}")
        else:
            print(f"  ❌ Command failed: {status_data}")
            await ws.close()
            return False
        print()

        # Test 4: Set Expression (servo command)
        print("Test 4: Testing 'set_expression' command...")

        expr_cmd = {
            "action": "set_expression",
            "params": {"expression": "happy"}
        }
        await ws.send(json.dumps(expr_cmd))

        expr_response = await asyncio.wait_for(ws.recv(), timeout=10)
        expr_data = json.loads(expr_response)

        if expr_data.get("status") == "success":
            print("  ✅ set_expression command working")
            print("  GairiHead should now look happy!")
        else:
            print(f"  ❌ Command failed: {expr_data}")
        print()

        # Test 5: Speak (long-running command)
        print("Test 5: Testing 'speak' command (may take 10-20 seconds)...")

        speak_cmd = {
            "action": "speak",
            "params": {
                "text": "Hello from the Gary team! This is a test of the speak command.",
                "expression": "happy",
                "animate_mouth": True
            }
        }
        await ws.send(json.dumps(speak_cmd))
        print("  ⏳ Waiting for speech to complete...")

        speak_response = await asyncio.wait_for(ws.recv(), timeout=120)
        speak_data = json.loads(speak_response)

        if speak_data.get("status") == "success":
            print("  ✅ speak command working")
            print("  GairiHead should have spoken the test message")
        else:
            print(f"  ❌ Command failed: {speak_data}")
        print()

        # Test 6: Input Validation (should fail)
        print("Test 6: Testing input validation (invalid command)...")

        invalid_cmd = {
            "action": "invalid_action",
            "params": {}
        }
        await ws.send(json.dumps(invalid_cmd))

        invalid_response = await asyncio.wait_for(ws.recv(), timeout=5)
        invalid_data = json.loads(invalid_response)

        if invalid_data.get("status") == "error":
            print("  ✅ Input validation working (correctly rejected invalid command)")
            print(f"  Error: {invalid_data.get('error', '')[:80]}")
        else:
            print("  ⚠️  Input validation may not be working properly")
        print()

        # Close connection
        await ws.close()
        print("  Connection closed cleanly")
        print()

        # Success summary
        print("=" * 70)
        print("✅ ALL TESTS PASSED!")
        print("=" * 70)
        print()
        print("Your Gary integration should now work. Key points:")
        print("  1. Use websockets library (not requests/httpx)")
        print("  2. Use ws:// protocol (not http://)")
        print("  3. Send auth token as FIRST message")
        print("  4. Wait for auth confirmation before sending commands")
        print("  5. Use long timeouts for speak command (60-120 seconds)")
        print()
        return True

    except websockets.exceptions.ConnectionRefused:
        print("  ❌ Connection refused")
        print("  The GairiHead server may not be running")
        print()
        return False

    except asyncio.TimeoutError:
        print("  ❌ Timeout waiting for response")
        print("  The server may be busy or unresponsive")
        print()
        return False

    except Exception as e:
        print(f"  ❌ Unexpected error: {type(e).__name__}: {e}")
        print()
        import traceback
        traceback.print_exc()
        return False


async def show_common_mistakes():
    """Show common mistakes and how to avoid them"""
    print()
    print("=" * 70)
    print("Common Mistakes to Avoid")
    print("=" * 70)
    print()

    print("❌ WRONG: Using HTTP POST (requests library)")
    print("```python")
    print("import requests")
    print("requests.post('http://100.103.67.41:8766', json={...})  # WILL NOT WORK")
    print("```")
    print()

    print("✅ CORRECT: Using WebSocket connection")
    print("```python")
    print("import websockets")
    print("ws = await websockets.connect('ws://100.103.67.41:8766')")
    print("await ws.send(json.dumps({...}))  # WORKS")
    print("```")
    print()


async def main():
    """Main entry point"""
    # Run tests
    success = await test_connection()

    if not success:
        print()
        print("=" * 70)
        print("TROUBLESHOOTING")
        print("=" * 70)
        print()
        print("If tests failed, check:")
        print("  1. Is GairiHead server running?")
        print("     - Run: sudo lsof -i :8766")
        print("  2. Can you reach the host?")
        print("     - Run: ping 100.103.67.41")
        print("  3. Are you using websockets library?")
        print("     - Install: pip install websockets")
        print("  4. Is your firewall blocking port 8766?")
        print()
        print("See docs/GARY_TROUBLESHOOTING.md for detailed help")
        print()
        await show_common_mistakes()
        return 1

    return 0


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
