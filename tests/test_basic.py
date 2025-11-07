#!/usr/bin/env python3
"""
Basic test - verify imports and config work
Run this BEFORE connecting servos
"""

import sys
sys.path.insert(0, '/home/tim/GairiHead/src')

print("=" * 60)
print("GairiHead Basic Test")
print("=" * 60)
print()

# Test 1: Imports
print("1. Testing imports...")
try:
    import yaml
    import loguru
    from gpiozero import Device
    print("   ✅ All imports successful")
except Exception as e:
    print(f"   ❌ Import failed: {e}")
    sys.exit(1)

# Test 2: Config loading
print("\n2. Testing config loading...")
try:
    with open('/home/tim/GairiHead/config/gairi_head.yaml', 'r') as f:
        config = yaml.safe_load(f)
    print(f"   ✅ Config loaded: {len(config)} sections")
    print(f"   - Hardware servos: {list(config['hardware']['servos'].keys())}")
except Exception as e:
    print(f"   ❌ Config failed: {e}")
    sys.exit(1)

# Test 3: Expression config
print("\n3. Testing expressions config...")
try:
    with open('/home/tim/GairiHead/config/expressions.yaml', 'r') as f:
        expressions = yaml.safe_load(f)
    expr_list = list(expressions['expressions'].keys())
    print(f"   ✅ Expressions loaded: {len(expr_list)}")
    print(f"   - Available: {', '.join(expr_list[:5])}...")
except Exception as e:
    print(f"   ❌ Expressions failed: {e}")
    sys.exit(1)

# Test 4: GPIO access
print("\n4. Testing GPIO access...")
try:
    import pigpio
    pi = pigpio.pi()
    if pi.connected:
        print("   ✅ pigpio daemon connected")
        pi.stop()
    else:
        print("   ⚠️  pigpio daemon not running")
        print("   Run: sudo systemctl start pigpiod")
except Exception as e:
    print(f"   ❌ GPIO test failed: {e}")

print()
print("=" * 60)
print("✅ Basic tests passed!")
print()
print("Next: Connect servos and run:")
print("   python tests/test_servos.py")
print("=" * 60)
