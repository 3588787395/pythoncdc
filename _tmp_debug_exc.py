#!/usr/bin/env python3
"""Detailed disassembly comparison for exception_handling_examples"""
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

orig_instrs = list(dis.get_instructions(orig_func))
decomp_instrs = list(dis.get_instructions(decomp_func))

print(f"Original: {len(orig_instrs)} instructions")
print(f"Decompiled: {len(decomp_instrs)} instructions")

min_len = min(len(orig_instrs), len(decomp_instrs))
for i in range(min_len):
    o = orig_instrs[i]
    d = decomp_instrs[i]
    if o.opname != d.opname or o.argval != d.argval:
        print(f"\nFirst difference at index {i}:")
        start = max(0, i - 10)
        end = min(min_len, i + 20)
        print(f"  {'Idx':>5s}  {'Orig':>55s}  {'Decomp':>55s}")
        for j in range(start, end):
            if j < len(orig_instrs) and j < len(decomp_instrs):
                oi = orig_instrs[j]
                di = decomp_instrs[j]
                marker = ">>>" if j == i else "   "
                print(f"  {marker} {j:3d}  {oi.offset:4d} {oi.opname:30s} {str(oi.argval):20s}  {di.offset:4d} {di.opname:30s} {str(di.argval):20s}")
        break
