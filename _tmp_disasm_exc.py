#!/usr/bin/env python3
"""Full disassembly of exception_handling_examples original vs decompiled"""
import sys
import dis
import marshal
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

def load_pyc_code(pyc_path):
    with open(pyc_path, 'rb') as f:
        f.read(16)
        return marshal.loads(f.read())

orig_code = load_pyc_code('python_syntax_comprehensive_test.pyc')
decomp_source = Path('python_syntax_comprehensive_testOK.py').read_text(encoding='utf-8')
decomp_code = compile(decomp_source, '<decompiled>', 'exec')

def find_func(code, name):
    for c in code.co_consts:
        if hasattr(c, 'co_code') and c.co_name == name:
            return c
    return None

orig_func = find_func(orig_code, 'exception_handling_examples')
decomp_func = find_func(decomp_code, 'exception_handling_examples')

print("=== ORIGINAL ===")
for i in dis.get_instructions(orig_func):
    print(f"  {i.offset:4d}: {i.opname:30s} {i.argval}")

print("\n=== DECOMPILED ===")
for i in dis.get_instructions(decomp_func):
    print(f"  {i.offset:4d}: {i.opname:30s} {i.argval}")
