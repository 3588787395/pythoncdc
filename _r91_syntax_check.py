#!/usr/bin/env python3
"""Check decompiled source for syntax errors"""
import sys
sys.path.insert(0, '.')
from pycdc import decompile_pyc

pyc_path = "site-packages/IQCommon/const.pyc"
try:
    decomp_src = decompile_pyc(pyc_path)
    lines = decomp_src.split('\n')
    print(f"Total lines: {len(lines)}")
    for i, line in enumerate(lines[:5]):
        print(f"  {i+1}: {line}")
    try:
        compile(decomp_src, '<decompiled>', 'exec')
        print("Compilation: OK")
    except SyntaxError as e:
        print(f"Syntax error: {e}")
        # Show the problematic line
        if e.lineno:
            for i, line in enumerate(lines):
                if i+1 == e.lineno:
                    print(f"  Line {e.lineno}: {line}")
                    break
except Exception as e:
    print(f"Error: {e}")
