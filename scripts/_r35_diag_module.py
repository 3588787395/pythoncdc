#!/usr/bin/env python3
"""R35 诊断: compare module-level bytecode of strategy_info_utils.pyc."""
import dis
import marshal
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

pyc_path = PROJECT_ROOT / 'site-packages/IQCommon/util/strategy_info_utils.pyc'
ok_path = PROJECT_ROOT / 'site-packages/IQCommon/util/strategy_info_utilsOK.py'

# Load original
with open(pyc_path, 'rb') as f:
    f.read(16)
    orig_code = marshal.load(f)

orig_instrs = list(dis.get_instructions(orig_code))
print(f"Original module: {len(orig_instrs)} instructions")

# Load decompiled
import py_compile
cfile = py_compile.compile(str(ok_path), doraise=True, quiet=2)
with open(cfile, 'rb') as f:
    f.read(16)
    decomp_code = marshal.load(f)

decomp_instrs = list(dis.get_instructions(decomp_code))
print(f"Decompiled module: {len(decomp_instrs)} instructions")

# Print side-by-side for first 60 instructions
print("\n=== First 60 instructions comparison ===")
for i in range(min(60, max(len(orig_instrs), len(decomp_instrs)))):
    o = orig_instrs[i] if i < len(orig_instrs) else None
    d = decomp_instrs[i] if i < len(decomp_instrs) else None
    o_str = f"{o.opname:35s} {repr(o.argval)[:60]}" if o else "(missing)"
    d_str = f"{d.opname:35s} {repr(d.argval)[:60]}" if d else "(missing)"
    # Normalize LOAD_ATTR/LOAD_METHOD
    o_op = o.opname if o else ""
    d_op = d.opname if d else ""
    if {o_op, d_op} == {'LOAD_ATTR', 'LOAD_METHOD'}:
        match = "OK*"
    elif o and d and o.opname == d.opname and o.argval == d.argval:
        match = "OK"
    else:
        match = "DIFF"
    print(f"  [{i:3d}] ORIG: {o_str:70s} | DECOMP: {d_str:70s} {match}")

# Print original module-level structure (imports, function defs, etc.)
print("\n=== Original module-level structure ===")
for i, instr in enumerate(orig_instrs):
    if instr.opname in ('MAKE_FUNCTION', 'STORE_NAME', 'STORE_GLOBAL',
                         'IMPORT_NAME', 'IMPORT_FROM', 'LOAD_CONST'):
        if hasattr(instr.argval, 'co_name'):
            print(f"  [{i:3d}] {instr.opname:35s} {instr.argval.co_name}")
        elif instr.argval is not None and not isinstance(instr.argval, str):
            print(f"  [{i:3d}] {instr.opname:35s} {type(instr.argval).__name__}")
        else:
            val = repr(instr.argval)[:60] if instr.argval is not None else 'None'
            print(f"  [{i:3d}] {instr.opname:35s} {val}")

# Count function definitions in original vs decompiled
orig_funcs = [i for i, instr in enumerate(orig_instrs) if instr.opname == 'MAKE_FUNCTION']
decomp_funcs = [i for i, instr in enumerate(decomp_instrs) if instr.opname == 'MAKE_FUNCTION']
print(f"\nOriginal MAKE_FUNCTION count: {len(orig_funcs)} at indices {orig_funcs}")
print(f"Decompiled MAKE_FUNCTION count: {len(decomp_funcs)} at indices {decomp_funcs}")

# Check original constants table
print(f"\n=== Original co_consts (first 20) ===")
for i, c in enumerate(orig_code.co_consts[:20]):
    if hasattr(c, 'co_name'):
        print(f"  const[{i}]: <code {c.co_name}>")
    else:
        print(f"  const[{i}]: {repr(c)[:80]}")

print(f"\n=== Decompiled co_consts (first 20) ===")
for i, c in enumerate(decomp_code.co_consts[:20]):
    if hasattr(c, 'co_name'):
        print(f"  const[{i}]: <code {c.co_name}>")
    else:
        print(f"  const[{i}]: {repr(c)[:80]}")
