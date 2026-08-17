#!/usr/bin/env python3
"""R94: Minimal repro - ternary condition_block with multiple user statements in except handler"""
import sys
sys.path.insert(0, 'f:/Downloads/pythoncdc-main')
sys.stdout.reconfigure(encoding='utf-8')

# Minimal source code that reproduces the issue:
# In an except handler, there are multiple statements before the ternary
# expression: error_info = func(); log.error(f"..."); x = a if cond else b

source = '''
def test_handler(symbol, fields):
    try:
        data = get_data(symbol)
        result = data if fields is None else data[fields]
    except BaseException:
        error_info = get_traceback()
        log.error(f"{symbol} error: {error_info}")
        result = EMPTY if fields is None else EMPTY[fields]
    return result
'''

# Compile to bytecode
code = compile(source, '<repro>', 'exec')

# Decompile using pycdc
from pycdc import decompile_pyc
import marshal, types, tempfile, os

# Write pyc file
with tempfile.NamedTemporaryFile(suffix='.pyc', delete=False, dir='.') as f:
    # Write pyc header
    import struct
    f.write(b'\x6f\x0d\x0d\x0a')  # magic for 3.11
    f.write(struct.pack('<I', 0))  # flags
    f.write(struct.pack('<II', 0, 0))  # timestamp + size
    marshal.dump(code, f)
    pyc_path = f.name

try:
    src = decompile_pyc(pyc_path)
    print("=== Decompiled source ===")
    print(src)
    
    # Check if system_log.error is present
    if 'log.error' in src:
        print("\n✓ PASS: log.error call is present in decompiled output")
    else:
        print("\n✗ FAIL: log.error call is MISSING from decompiled output")
        
    # Check if error_info assignment is present
    if 'error_info' in src:
        print("✓ PASS: error_info assignment is present")
    else:
        print("✗ FAIL: error_info assignment is MISSING")
        
finally:
    os.unlink(pyc_path)
