#!/usr/bin/env python3
"""
Test GairiHead websocket server locally
Run from GairiHead directory
"""

import asyncio
import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from loguru import logger


async def test_server_commands():
    """Test server commands via websocket"""
    import websockets

    server_url = "ws://localhost:8766"

    logger.info(f"Connecting to {server_url}...")

    try:
        async with websockets.connect(server_url, timeout=5) as ws:
            logger.success("✅ Connected to GairiHead server")

            # Test 1: Get status
            logger.info("\n1. Testing get_status...")
            await ws.send(json.dumps({'action': 'get_status', 'params': {}}))
            response = json.loads(await ws.recv())
            logger.info(f"Status: {json.dumps(response, indent=2)}")

            # Test 2: Detect faces
            logger.info("\n2. Testing detect_faces...")
            await ws.send(json.dumps({'action': 'detect_faces', 'params': {}}))
            response = json.loads(await ws.recv())
            logger.info(f"Faces: {response['data']['faces_detected']}")

            # Test 3: Capture snapshot
            logger.info("\n3. Testing capture_snapshot...")
            await ws.send(json.dumps({'action': 'capture_snapshot', 'params': {'quality': 85}}))
            response = json.loads(await ws.recv())
            if response['status'] == 'success':
                img_size = len(response['data']['image'])
                logger.success(f"✅ Captured {img_size} bytes")

            # Test 4: Set expression
            logger.info("\n4. Testing set_expression...")
            await ws.send(json.dumps({'action': 'set_expression', 'params': {'expression': 'happy'}}))
            response = json.loads(await ws.recv())
            logger.info(f"Expression: {response}")

            # Reset expression
            await ws.send(json.dumps({'action': 'set_expression', 'params': {'expression': 'idle'}}))
            response = json.loads(await ws.recv())

            logger.success("\n✅ All tests passed!")

    except asyncio.TimeoutError:
        logger.error("❌ Connection timeout - is server running?")
        logger.info("Start server with: python src/gairi_head_server.py")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("GairiHead Websocket Server Test")
    logger.info("=" * 60)

    asyncio.run(test_server_commands())
