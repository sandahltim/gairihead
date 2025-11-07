#!/usr/bin/env python3
"""
LLM Tier Manager - Two-tier intelligence for cost optimization

Tier 1: Local LLM (Llama 3.2 3B via Ollama) - Free, ~60% of queries
Tier 2: Cloud LLM (Claude Haiku 3.5/4.5) - Paid, ~40% of queries

Decision logic:
- Simple queries, greetings, status → Local
- Complex reasoning, tool calling, business logic → Cloud
- Confidence-based escalation
"""

import requests
import json
import time
from loguru import logger

class LLMTierManager:
    """Manages two-tier LLM system for cost optimization"""

    def __init__(self, config):
        """
        Initialize LLM tier manager

        Args:
            config: Configuration dict from gairi_head.yaml
        """
        self.config = config.get('intelligence', {})

        # Tier 1: Local LLM
        self.local_config = self.config.get('local_llm', {})
        self.local_enabled = self.local_config.get('enabled', True)
        self.local_model = self.local_config.get('model', 'llama3.2:3b')
        self.local_host = self.local_config.get('host', 'http://localhost:11434')
        self.local_temperature = self.local_config.get('temperature', 0.7)
        self.local_max_tokens = self.local_config.get('max_tokens', 150)
        self.local_timeout = self.local_config.get('timeout', 5000) / 1000.0

        # Tier 2: Cloud LLM (Haiku)
        self.cloud_config = self.config.get('haiku', {})
        self.cloud_enabled = self.cloud_config.get('enabled', True)
        self.cloud_ws_url = self.cloud_config.get('websocket_url', 'ws://localhost:8765/ws')
        self.cloud_retry_attempts = self.cloud_config.get('retry_attempts', 3)
        self.escalation_threshold = self.cloud_config.get('escalation_threshold', 0.7)

        # Statistics
        self.stats = {
            'total_queries': 0,
            'local_queries': 0,
            'cloud_queries': 0,
            'escalations': 0,
            'local_failures': 0,
            'cloud_failures': 0
        }

        logger.info(f"LLMTierManager initialized (Local: {self.local_enabled}, Cloud: {self.cloud_enabled})")

    def query(self, prompt, context=None, force_tier=None):
        """
        Query LLM with automatic tier selection

        Args:
            prompt: User prompt
            context: Optional context/history
            force_tier: Force specific tier ('local' or 'cloud')

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

        # Determine tier
        if force_tier == 'cloud':
            tier = 'cloud'
        elif force_tier == 'local':
            tier = 'local'
        else:
            tier = self._select_tier(prompt, context)

        logger.debug(f"Query tier: {tier}")

        # Execute query
        if tier == 'local':
            result = self._query_local(prompt, context)

            # Check if should escalate
            if result and result.get('confidence', 1.0) < self.escalation_threshold:
                logger.info(f"Escalating to cloud (confidence: {result.get('confidence', 0):.2f})")
                self.stats['escalations'] += 1
                cloud_result = self._query_cloud(prompt, context)

                if cloud_result:
                    result = cloud_result
                    result['escalated'] = True

        else:
            result = self._query_cloud(prompt, context)

        # Add metadata
        if result:
            result['tier'] = tier
            result['time_ms'] = int((time.time() - start_time) * 1000)
            result['escalated'] = result.get('escalated', False)

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

    def _query_local(self, prompt, context):
        """
        Query local Ollama LLM

        Args:
            prompt: User prompt
            context: Optional context

        Returns:
            dict: Response data or None on failure
        """
        if not self.local_enabled:
            logger.debug("Local LLM disabled")
            return None

        try:
            # Build request
            messages = []

            if context:
                messages.append({
                    'role': 'system',
                    'content': context
                })

            messages.append({
                'role': 'user',
                'content': prompt
            })

            # Call Ollama API
            url = f"{self.local_host}/api/chat"
            payload = {
                'model': self.local_model,
                'messages': messages,
                'stream': False,
                'options': {
                    'temperature': self.local_temperature,
                    'num_predict': self.local_max_tokens
                }
            }

            response = requests.post(url, json=payload, timeout=self.local_timeout)
            response.raise_for_status()

            data = response.json()

            # Extract response
            result = {
                'response': data.get('message', {}).get('content', ''),
                'confidence': 0.8,  # Placeholder - could analyze response quality
                'tokens': data.get('eval_count', 0),
                'model': self.local_model
            }

            self.stats['local_queries'] += 1
            logger.debug(f"Local LLM response ({result['tokens']} tokens)")

            return result

        except requests.exceptions.Timeout:
            logger.warning(f"Local LLM timeout ({self.local_timeout}s)")
            self.stats['local_failures'] += 1
            return None

        except Exception as e:
            logger.error(f"Local LLM error: {e}")
            self.stats['local_failures'] += 1
            return None

    def _query_cloud(self, prompt, context):
        """
        Query cloud LLM (full GAiRI via main Gary websocket)

        Args:
            prompt: User prompt
            context: Optional context

        Returns:
            dict: Response data or None on failure
        """
        if not self.cloud_enabled:
            logger.debug("Cloud LLM disabled")
            return None

        try:
            import websocket
            import json

            # Build full prompt with context
            if context:
                full_prompt = f"{context}\n\nUser: {prompt}"
            else:
                full_prompt = prompt

            # Connect to main Gary websocket
            ws = websocket.create_connection(
                self.cloud_ws_url,
                timeout=10
            )

            logger.debug(f"Connected to Gary at {self.cloud_ws_url}")

            # Send prompt
            ws.send(full_prompt)

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
                'confidence': 1.0,  # Full Gary responses are high confidence
                'tokens': len(response_text.split()),  # Rough estimate
                'model': 'gairi-full'
            }

            self.stats['cloud_queries'] += 1
            logger.debug(f"Cloud LLM (GAiRI) response ({result['tokens']} tokens)")

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
