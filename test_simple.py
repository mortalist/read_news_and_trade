#!/usr/bin/env python
# 가장 간단한 테스트
print("=" * 60)
print("TEST 1: Python is running!")
print("=" * 60)

import sys
print(f"TEST 2: Python version: {sys.version}")

import os
print(f"TEST 3: Current directory: {os.getcwd()}")

print("\nTEST 4: Trying to import yaml...")
try:
    import yaml
    print("✅ yaml imported successfully")
except Exception as e:
    print(f"❌ yaml import failed: {e}")

print("\nTEST 5: Trying to import openai...")
try:
    import openai
    print("✅ openai imported successfully")
except Exception as e:
    print(f"❌ openai import failed: {e}")

print("\nTEST 6: Trying to import feedparser...")
try:
    import feedparser
    print("✅ feedparser imported successfully")
except Exception as e:
    print(f"❌ feedparser import failed: {e}")

print("\nTEST 7: Checking config.yaml...")
config_path = "config.yaml"
if os.path.exists(config_path):
    print(f"✅ config.yaml exists")
    with open(config_path, 'r') as f:
        import yaml
        config = yaml.safe_load(f)
        print(f"✅ config.yaml loaded")
        print(f"   USE_KIS_API: {config.get('USE_KIS_API')}")
        print(f"   USE_DISCORD: {config.get('USE_DISCORD')}")
        has_key = config.get('OPENAI_API_KEY', '').startswith('sk-')
        print(f"   Has valid API key: {has_key}")
else:
    print(f"❌ config.yaml not found")

print("\n" + "=" * 60)
print("All tests completed!")
print("=" * 60)
