#!/usr/bin/env python3
"""
Test GairiHead server commands
Shows how to properly call the WebSocket API
"""

import asyncio
import json
import websockets

GAIRIHEAD_SERVER = "ws://100.103.67.41:8766"  # GairiHead's Tailscale IP


async def test_speak():
    """Test speak command"""
    print("Testing speak command...")

    async with websockets.connect(GAIRIHEAD_SERVER) as ws:
        command = {
            "action": "speak",
            "params": {
                "text": "Hello from Gary! This is a test of the speak command.",
                "expression": "happy"
            }
        }

        await ws.send(json.dumps(command))
        response = await ws.recv()
        result = json.loads(response)

        print(f"Response: {result}")
        return result


async def test_expression():
    """Test set_expression command"""
    print("\nTesting expression commands...")

    expressions = ["sarcasm", "thinking", "alert", "idle"]

    for expr in expressions:
        async with websockets.connect(GAIRIHEAD_SERVER) as ws:
            command = {
                "action": "set_expression",
                "params": {
                    "expression": expr
                }
            }

            await ws.send(json.dumps(command))
            response = await ws.recv()
            result = json.loads(response)

            print(f"Expression '{expr}': {result['status']}")
            await asyncio.sleep(1.5)  # Wait between expressions


async def test_get_status():
    """Test get_status command"""
    print("\nTesting get_status command...")

    async with websockets.connect(GAIRIHEAD_SERVER) as ws:
        command = {
            "action": "get_status",
            "params": {}
        }

        await ws.send(json.dumps(command))
        response = await ws.recv()
        result = json.loads(response)

        print(f"Status: {json.dumps(result, indent=2)}")
        return result


async def main():
    """Run all tests"""
    print("=" * 60)
    print("GairiHead Server Command Test")
    print("=" * 60)

    try:
        # Test status
        await test_get_status()

        # Test speak
        await test_speak()

        # Test expressions
        await test_expression()

        print("\n" + "=" * 60)
        print("✅ All tests completed!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
