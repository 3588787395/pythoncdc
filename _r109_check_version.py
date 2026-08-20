"""Check Python version of original pyc"""
import struct

pyc_path = '.trae/specs/decompiler-test-comprehensive-10rounds/rounds/round_02/test_engineer/minimal_repros/repro_r2_10_try_wrap_for_else_break.pyc'
with open(pyc_path, 'rb') as f:
    magic = f.read(4)
    print(f"Magic: {magic.hex()}")
    flags = struct.unpack('<I', f.read(4))[0]
    print(f"Flags: {flags}")
    # Python 3.11 magic numbers: 0x0A0D0D0A (3495) or similar
    # 3495 = Python 3.11
    magic_num = struct.unpack('<H', magic[:2])[0]
    print(f"Magic number: {magic_num}")
    
    # Check Python version from magic
    # 3495 = Python 3.11
    # 3531 = Python 3.12
    if magic_num >= 3495 and magic_num < 3531:
        print("Python 3.11")
    elif magic_num >= 3531:
        print("Python 3.12+")
    else:
        print(f"Unknown Python version (magic={magic_num})")

# Also check current Python version
import sys
print(f"\nCurrent Python: {sys.version}")
print(f"Current Python magic: {importlib.util.MAGIC_NUMBER.hex()}")
import importlib
print(f"Current Python magic: {importlib.util.MAGIC_NUMBER.hex()}")
