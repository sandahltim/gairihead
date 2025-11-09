#!/usr/bin/env python3
"""
Test WebSocket Authentication
Verifies that the API token authentication is working correctly
"""

import asyncio
import json
import websockets
import sys

# Test configuration
HOST = "localhost"
PORT = 8766
VALID_TOKEN = "av-UQ9Eh64ZcbRPadshCzpqiVkG5Rw2QxDTuJYRU__o"
INVALID_TOKEN = "invalid-token-123"

async def test_valid_auth():
    """Test connection with valid token"""
    print("Test 1: Valid authentication...")
    try:
        async with websockets.connect(f'ws://{HOST}:{PORT}') as ws:
            # Send authentication
            await ws.send(json.dumps({'token': VALID_TOKEN}))
            auth_response = json.loads(await ws.recv())

            if auth_response.get('status') == 'authenticated':
                print("  ✅ Authentication successful")

                # Test a command
                await ws.send(json.dumps({'action': 'get_status', 'params': {}}))
                status_response = json.loads(await ws.recv())

                if status_response.get('status') == 'success':
                    print("  ✅ Command executed successfully")
                    return True
                else:
                    print(f"  ❌ Command failed: {status_response}")
                    return False
            else:
                print(f"  ❌ Authentication failed: {auth_response}")
                return False

    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

async def test_invalid_auth():
    """Test connection with invalid token"""
    print("\nTest 2: Invalid authentication (should fail)...")
    try:
        async with websockets.connect(f'ws://{HOST}:{PORT}') as ws:
            # Send invalid token
            await ws.send(json.dumps({'token': INVALID_TOKEN}))
            auth_response = json.loads(await ws.recv())

            if auth_response.get('status') == 'error':
                print("  ✅ Correctly rejected invalid token")
                return True
            else:
                print(f"  ❌ Should have rejected invalid token: {auth_response}")
                return False

    except websockets.exceptions.ConnectionClosed:
        print("  ✅ Connection closed by server (expected)")
        return True
    except Exception as e:
        print(f"  ❌ Unexpected error: {e}")
        return False

async def test_no_auth():
    """Test connection without authentication"""
    print("\nTest 3: No authentication (should timeout/fail)...")
    try:
        async with websockets.connect(f'ws://{HOST}:{PORT}') as ws:
            # Try to send command without authenticating
            await ws.send(json.dumps({'action': 'get_status', 'params': {}}))

            # Should timeout or get error
            response = await asyncio.wait_for(ws.recv(), timeout=6.0)
            print(f"  ❌ Should have been rejected: {response}")
            return False

    except asyncio.TimeoutError:
        print("  ✅ Connection timed out (expected)")
        return True
    except websockets.exceptions.ConnectionClosed:
        print("  ✅ Connection closed by server (expected)")
        return True
    except Exception as e:
        print(f"  ⚠️  Error (may be expected): {e}")
        return True

async def test_input_validation():
    """Test input validation"""
    print("\nTest 4: Input validation...")
    try:
        async with websockets.connect(f'ws://{HOST}:{PORT}') as ws:
            # Authenticate
            await ws.send(json.dumps({'token': VALID_TOKEN}))
            await ws.recv()  # Consume auth response

            # Test invalid action
            await ws.send(json.dumps({'action': 'invalid_command', 'params': {}}))
            response = json.loads(await ws.recv())

            if response.get('status') == 'error' and 'Unknown action' in response.get('error', ''):
                print("  ✅ Invalid action rejected")
            else:
                print(f"  ❌ Should have rejected invalid action: {response}")
                return False

            # Test invalid parameter
            await ws.send(json.dumps({'action': 'speak', 'params': {'text': 'x' * 6000}}))
            response = json.loads(await ws.recv())

            if response.get('status') == 'error' and 'exceeds maximum length' in response.get('error', ''):
                print("  ✅ Invalid parameter rejected")
                return True
            else:
                print(f"  ❌ Should have rejected long text: {response}")
                return False

    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

async def main():
    """Run all tests"""
    print("=" * 60)
    print("GairiHead WebSocket Authentication Test")
    print("=" * 60)
    print(f"\nTesting server at ws://{HOST}:{PORT}")
    print(f"Using token: {VALID_TOKEN[:20]}...\n")

    # Check if server is running
    try:
        async with websockets.connect(f'ws://{HOST}:{PORT}') as ws:
            pass
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        print("\nMake sure the GairiHead server is running:")
        print("  cd ~/GairiHead")
        print("  source venv/bin/activate")
        print("  python src/gairi_head_server.py")
        sys.exit(1)

    # Run tests
    results = []
    results.append(await test_valid_auth())
    results.append(await test_invalid_auth())
    results.append(await test_no_auth())
    results.append(await test_input_validation())

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")

    if passed == total:
        print("\n✅ All tests passed! Authentication is working correctly.")
        return 0
    else:
        print(f"\n❌ {total - passed} test(s) failed.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
