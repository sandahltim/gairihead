#!/usr/bin/env python3
"""
LLM Tier Manager - Two-tier intelligence for cost optimization

Version: 2.1 (2025-11-07) - Added training data collection
Tier 1: Local LLM (Qwen 2.5 Coder 7B on Gary's server) - Free, ~60% of queries
Tier 2: Cloud LLM (Claude Haiku 4.5) - Paid, ~40% of queries

Decision logic:
- Simple queries, greetings, status → Local (Qwen on Gary's server)
- Complex reasoning, tool calling, business logic → Cloud (Haiku)
- Confidence-based escalation
- Authorization-aware: Strangers get local only, main users get full access

Training Data Collection (v2.1):
- Logs all main user (Level 1) conversations for fine-tuning
- Captures Qwen responses and Haiku escalations
- Security: NEVER logs stranger (Level 3) interactions
"""

import requests
import json
import time
import websocket
from loguru import logger

class LLMTierManager:
    """Manages two-tier LLM system for cost optimization"""

    def __init__(self, config, authorization_manager=None):
        """
        Initialize LLM tier manager

        Args:
            config: Configuration dict from gairi_head.yaml
            authorization_manager: Face recognition manager for authorization levels
        """
        self.config = config.get('intelligence', {})
        self.authorization_manager = authorization_manager

        # Gary's websocket URL (v2.0 - routes through Gary server)
        self.gary_ws_url = self.config.get('gary_websocket_url', 'ws://localhost:8765/ws')
        self.gary_timeout = 10.0  # seconds

        # Tier settings
        self.local_enabled = True  # Always enabled (routes through Gary)
        self.cloud_enabled = True  # Always enabled (routes through Gary)
        self.escalation_threshold = self.config.get('escalation_threshold', 0.7)

        # Statistics
        self.stats = {
            'total_queries': 0,
            'local_queries': 0,
            'cloud_queries': 0,
            'escalations': 0,
            'local_failures': 0,
            'cloud_failures': 0
        }

        logger.info(f"LLMTierManager v2.1 initialized (routes through Gary at {self.gary_ws_url})")
        logger.info(f"✅ Training data collection happens on Gary's server")

    def query(self, prompt, context=None, force_tier=None, authorization=None):
        """
        Query LLM with automatic tier selection and authorization

        Args:
            prompt: User prompt
            context: Optional context/history
            force_tier: Force specific tier ('local' or 'cloud')
            authorization: Authorization context from face recognition

        Returns:
            dict: {
                'response': str,
                'tier': 'local' or 'cloud',
                'confidence': float,
                'escalated': bool,
                'tokens': int,
                'time_ms': int
            }
        """
        start_time = time.time()
        self.stats['total_queries'] += 1

        # Security: Strangers (level 3) are ALWAYS local-only (v2.0)
        if authorization and authorization.get('level') == 3:
            logger.warning("🚫 Stranger detected - forcing local tier (no cloud/Haiku access)")
            tier = 'local'
            force_tier = 'local'  # Block escalation
        # Determine tier
        elif force_tier == 'cloud':
            tier = 'cloud'
        elif force_tier == 'local':
            tier = 'local'
        else:
            tier = self._select_tier(prompt, context)

        logger.debug(f"Query tier: {tier} (auth level: {authorization.get('level') if authorization else 'N/A'})")

        # Execute query
        if tier == 'local':
            result = self._query_local(prompt, context, authorization)

            # Check if should escalate (NOT for strangers)
            should_escalate = (
                result and
                result.get('confidence', 1.0) < self.escalation_threshold and
                (not authorization or authorization.get('level') != 3)  # No escalation for strangers
            )

            if should_escalate:
                logger.info(f"Escalating to cloud (confidence: {result.get('confidence', 0):.2f})")
                self.stats['escalations'] += 1
                cloud_result = self._query_cloud(prompt, context, authorization)

                if cloud_result:
                    result = cloud_result
                    result['escalated'] = True

        else:
            result = self._query_cloud(prompt, context, authorization)

        # Add metadata
        if result:
            result['tier'] = tier
            result['time_ms'] = int((time.time() - start_time) * 1000)
            result['escalated'] = result.get('escalated', False)

        # v2.1 (2025-11-07): Training data logging happens on Gary's server
        # Gary logs all GairiHead interactions via websocket handler

        return result

    def _select_tier(self, prompt, context):
        """
        Select appropriate tier based on query complexity

        Args:
            prompt: User prompt
            context: Optional context

        Returns:
            str: 'local' or 'cloud'
        """
        # Keywords that indicate cloud tier needed
        cloud_keywords = [
            'customer', 'contract', 'order', 'invoice', 'schedule',
            'delivery', 'pickup', 'equipment', 'revenue', 'profit',
            'analyze', 'calculate', 'report', 'find', 'search'
        ]

        # Keywords that local can handle
        local_keywords = [
            'hello', 'hi', 'hey', 'good morning', 'good afternoon',
            'how are you', 'what time', 'weather', 'thanks', 'thank you'
        ]

        prompt_lower = prompt.lower()

        # Check for cloud keywords
        if any(keyword in prompt_lower for keyword in cloud_keywords):
            return 'cloud'

        # Check for local keywords
        if any(keyword in prompt_lower for keyword in local_keywords):
            return 'local'

        # Default to local for simple/short queries
        if len(prompt.split()) < 10:
            return 'local'

        # Complex/long queries go to cloud
        return 'cloud'

    def _query_local(self, prompt, context, authorization=None):
        """
        Query local LLM (Qwen on Gary's server) via websocket

        Args:
            prompt: User prompt
            context: Optional context
            authorization: Authorization context from face recognition

        Returns:
            dict: Response data or None on failure
        """
        if not self.local_enabled:
            logger.debug("Local LLM disabled")
            return None

        try:
            # Build JSON message for Gary
            # v2.0: Routes through Gary's server instead of local Ollama
            message = {
                'text': prompt,
                'source': 'gairihead',
                'tier_preference': 'local',  # Request local LLM (Qwen)
                'authorization': authorization or {
                    'level': 3,  # Default: stranger mode
                    'user': 'unknown',
                    'confidence': 0.0
                }
            }

            # Connect to Gary websocket
            ws = websocket.create_connection(
                self.gary_ws_url,
                timeout=self.gary_timeout
            )

            logger.debug(f"Connected to Gary at {self.gary_ws_url} (local tier)")

            # Send JSON request
            ws.send(json.dumps(message))

            # Receive response (text)
            response_text = ws.recv()

            ws.close()

            result = {
                'response': response_text,
                'confidence': 0.8,  # Local model confidence
                'tokens': len(response_text.split()),
                'model': 'qwen-local'
            }

            self.stats['local_queries'] += 1
            logger.debug(f"Local LLM (Gary) response ({result['tokens']} tokens)")

            return result

        except Exception as e:
            logger.error(f"Local LLM error: {e}")
            self.stats['local_failures'] += 1
            return None

    def _query_cloud(self, prompt, context, authorization=None):
        """
        Query cloud LLM (Claude Haiku via Gary websocket)

        Args:
            prompt: User prompt
            context: Optional context
            authorization: Authorization context from face recognition

        Returns:
            dict: Response data or None on failure
        """
        if not self.cloud_enabled:
            logger.debug("Cloud LLM disabled")
            return None

        try:
            # Build JSON message for Gary
            # v2.0: Routes through Gary with cloud tier preference
            message = {
                'text': prompt,
                'source': 'gairihead',
                'tier_preference': 'cloud',  # Request cloud LLM (Haiku)
                'authorization': authorization or {
                    'level': 3,  # Default: stranger mode
                    'user': 'unknown',
                    'confidence': 0.0
                }
            }

            # Connect to Gary websocket
            ws = websocket.create_connection(
                self.gary_ws_url,
                timeout=self.gary_timeout
            )

            logger.debug(f"Connected to Gary at {self.gary_ws_url} (cloud tier)")

            # Send JSON request
            ws.send(json.dumps(message))

            # Receive response (text)
            response_text = ws.recv()

            # Receive trace events (may arrive)
            # Note: Gary sends tool execution traces as JSON, then final text
            # We just want final text, so read until we get non-JSON or timeout
            while True:
                try:
                    # Try to parse as JSON (trace event)
                    test_json = json.loads(response_text)
                    logger.debug(f"Trace event: {test_json.get('type', 'unknown')}")
                    # Get next message
                    response_text = ws.recv()
                except json.JSONDecodeError:
                    # Not JSON, this is the final text response
                    break
                except Exception:
                    # Timeout or other error, use what we have
                    break

            ws.close()

            result = {
                'response': response_text,
                'confidence': 1.0,  # Full Gary (Haiku) responses are high confidence
                'tokens': len(response_text.split()),  # Rough estimate
                'model': 'haiku-cloud'
            }

            self.stats['cloud_queries'] += 1
            logger.debug(f"Cloud LLM (Haiku via Gary) response ({result['tokens']} tokens)")

            return result

        except Exception as e:
            logger.error(f"Cloud LLM error: {e}")
            self.stats['cloud_failures'] += 1
            return None

    def get_stats(self):
        """
        Get usage statistics

        Returns:
            dict: Usage stats
        """
        stats = self.stats.copy()

        # Calculate percentages
        if stats['total_queries'] > 0:
            stats['local_percentage'] = (stats['local_queries'] / stats['total_queries']) * 100
            stats['cloud_percentage'] = (stats['cloud_queries'] / stats['total_queries']) * 100
        else:
            stats['local_percentage'] = 0
            stats['cloud_percentage'] = 0

        return stats

    def reset_stats(self):
        """Reset usage statistics"""
        self.stats = {
            'total_queries': 0,
            'local_queries': 0,
            'cloud_queries': 0,
            'escalations': 0,
            'local_failures': 0,
            'cloud_failures': 0
        }
        logger.info("Statistics reset")


# Example usage and testing
if __name__ == '__main__':
    import yaml
    from loguru import logger
    import sys

    # Configure logging
    logger.remove()
    logger.add(sys.stderr, level="DEBUG")

    print("LLMTierManager Test")
    print("=" * 60)

    # Load config
    with open('/home/tim/GairiHead/config/gairi_head.yaml', 'r') as f:
        config = yaml.safe_load(f)

    # Initialize manager
    manager = LLMTierManager(config)

    # Test queries
    test_queries = [
        ("Hello, how are you?", 'local'),
        ("What's the weather like?", 'local'),
        ("Show me customer XYZ's contracts", 'cloud'),
        ("Calculate total revenue for Q4", 'cloud'),
        ("Thanks!", 'local')
    ]

    print("\nTesting tier selection:")
    for query, expected_tier in test_queries:
        result = manager.query(query)

        if result:
            tier = result['tier']
            match = "✅" if tier == expected_tier else "❌"
            print(f"  {match} '{query[:40]}...' → {tier} (expected {expected_tier})")
        else:
            print(f"  ❌ '{query[:40]}...' → FAILED")

    # Show stats
    print("\n" + "=" * 60)
    print("Statistics:")
    stats = manager.get_stats()
    print(f"  Total queries: {stats['total_queries']}")
    print(f"  Local: {stats['local_queries']} ({stats['local_percentage']:.1f}%)")
    print(f"  Cloud: {stats['cloud_queries']} ({stats['cloud_percentage']:.1f}%)")
    print(f"  Escalations: {stats['escalations']}")
    print(f"  Local failures: {stats['local_failures']}")
    print(f"  Cloud failures: {stats['cloud_failures']}")

    print("\n✅ LLMTierManager test complete")
