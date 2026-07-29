#!/usr/bin/env python3
"""Show first divergence in load_bars_from_hundsun bytecode."""
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

# Compile the decompiled source and find the function
with open('/tmp/r10_decompiled.py', 'r', encoding='utf-8') as f:
    src = f.read()
compiled = compile(src, '<decompiled>', 'exec')
# Find the load_bars_from_hundsun code object in compiled
def find2(co, n):
    if co.co_name == n:
        return co
    for k in co.co_consts:
        if isinstance(k, types.CodeType):
            r = find2(k, n)
            if r:
                return r
    return None
new = find2(compiled, 'load_bars_from_hundsun')
new_instrs = list(dis.get_instructions(new))

print(f"ORIG instrs: {len(orig_instrs)}, NEW instrs: {len(new_instrs)}")
print(f"\n=== FIRST DIVERGENCE ===")
maxlen = max(len(orig_instrs), len(new_instrs))
first_diff = None
for i in range(maxlen):
    o = orig_instrs[i] if i < len(orig_instrs) else None
    n = new_instrs[i] if i < len(new_instrs) else None
    o_str = f"{o.offset:4d} {o.opname:30s} {o.argval}" if o else "<none>"
    n_str = f"{n.offset:4d} {n.opname:30s} {n.argval}" if n else "<none>"
    if o_str != n_str:
        if first_diff is None:
            first_diff = i
        print(f"  idx{i:3d} | ORIG: {o_str:55s} | NEW: {n_str}")
        if i > first_diff + 30:
            print("  ... (truncated)")
            break

# Show context around first diff
if first_diff is not None:
    print(f"\n=== CONTEXT around idx {first_diff} ===")
    lo = max(0, first_diff - 5)
    hi = min(maxlen, first_diff + 20)
    for i in range(lo, hi):
        o = orig_instrs[i] if i < len(orig_instrs) else None
        n = new_instrs[i] if i < len(new_instrs) else None
        o_str = f"{o.offset:4d} {o.opname:28s} {o.argval}" if o else "<none>"
        n_str = f"{n.offset:4d} {n.opname:28s} {n.argval}" if n else "<none>"
        mark = ">>" if i == first_diff else "  "
        print(f"{mark} idx{i:3d} | O: {o_str:50s} | N: {n_str}")
