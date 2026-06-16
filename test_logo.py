"""Test if logo file can be loaded"""
import os
import sys
from pathlib import Path
import base64

# Reconfigure stdout to support UTF-8 characters like emojis in Windows terminal
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

print("Testing logo file loading...")
print("=" * 60)

# Test 1: Check if file exists
logo_file = "lingual_logo.png"
print(f"\n1. Checking if '{logo_file}' exists...")
if os.path.exists(logo_file):
    print(f"   ✅ File found!")
    file_size = os.path.getsize(logo_file)
    print(f"   File size: {file_size} bytes")
else:
    print(f"   ❌ File NOT found!")
    exit(1)

# Test 2: Try to read the file
print(f"\n2. Trying to read the file...")
try:
    with open(logo_file, "rb") as f:
        data = f.read()
    print(f"   ✅ File read successfully!")
    print(f"   Read {len(data)} bytes")
except Exception as e:
    print(f"   ❌ Error reading file: {e}")
    exit(1)

# Test 3: Try to encode as base64
print(f"\n3. Trying to encode as base64...")
try:
    encoded = base64.b64encode(data).decode()
    print(f"   ✅ Encoded successfully!")
    print(f"   Encoded length: {len(encoded)} characters")
    print(f"   First 50 chars: {encoded[:50]}...")
except Exception as e:
    print(f"   ❌ Error encoding: {e}")
    exit(1)

# Test 4: Check with Path
print(f"\n4. Testing with pathlib.Path...")
path = Path(logo_file)
if path.exists():
    print(f"   ✅ Path exists!")
    print(f"   Absolute path: {path.absolute()}")
else:
    print(f"   ❌ Path not found!")

print("\n" + "=" * 60)
print("✅ ALL TESTS PASSED!")
print("=" * 60)
print("\nThe logo file is working correctly.")
print("If you still see the error in Streamlit:")
print("1. Stop the Streamlit app (Ctrl+C)")
print("2. Clear browser cache (Ctrl+Shift+R)")
print("3. Restart: streamlit run app.py")
