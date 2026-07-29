#!/usr/bin/env python3
"""Dump original load_bars_from_hundsun bytecode between offsets 1700-2100."""
import sys, types, dis
sys.path.insert(0, '/workspace')
from core.pyc_loader_v2 import load_pyc_file_v2

m = load_pyc_file_v2('/workspace/quotation.pyc')
c = m.code.get() if hasattr(m.code, 'get') else m.code
if hasattr(c, 'to_python_code'):
    c = c.to_python_code()

def find(co, n):
    if co.co_name == n:
        return co
    for k in co.co_consts:
        if isinstance(k, types.CodeType):
            r = find(k, n)
            if r:
                return r
    return None

orig = find(c, 'load_bars_from_hundsun')
orig_instrs = list(dis.get_instructions(orig))

print("=== ORIGINAL bytecode offsets 1690-2100 ===")
for ins in orig_instrs:
    if 1690 <= ins.offset <= 2100:
        print(f"  {ins.offset:4d} {ins.opname:30s} {ins.argval}")

print("\n=== ORIGINAL bytecode offsets 2060-2200 (after if body) ===")
for ins in orig_instrs:
    if 2060 <= ins.offset <= 2200:
        print(f"  {ins.offset:4d} {ins.opname:30s} {ins.argval}")

# Also count instructions
print(f"\nORIG total instrs: {len(orig_instrs)}")
