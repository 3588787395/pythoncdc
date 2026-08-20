"""Debug the copy_blocks detection for repro_r11_06."""
import sys
sys.path.insert(0, 'f:/Downloads/pythoncdc-main')

import marshal
import types

with open('.trae/specs/decompiler-test-comprehensive-10rounds/rounds/round_11/test_engineer/minimal_repros/repro_r11_06_try_except_finally_continue.pyc', 'rb') as f:
    f.read(16)
    code = marshal.load(f)

from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer

builder = CFGBuilder()
cfg = builder.build(code)

# Get the finally body block (154)
finally_block = cfg.get_block_by_offset(154)
print(f"Finally block @{finally_block.start_offset}:")
for instr in finally_block.instructions:
    print(f"  {instr.offset:4d} {instr.opname:30s} {instr.argval}")

# Extract ops between PUSH_EXC_INFO and RERAISE
_m = [i for i in finally_block.instructions if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
print(f"\nFiltered instructions: {[(i.opname, i.argval) for i in _m]}")

_push = any(i.opname == 'PUSH_EXC_INFO' for i in _m)
_reraise = any(i.opname == 'RERAISE' for i in _m)
print(f"has_push={_push}, has_reraise={_reraise}")

_s = None
_e = None
for _si, _instr in enumerate(_m):
    if _instr.opname == 'PUSH_EXC_INFO' and _s is None:
        _s = _si + 1
    if _instr.opname == 'RERAISE' and _s is not None:
        _e = _si
        break

print(f"_s={_s}, _e={_e}")
if _s is not None and _e is not None:
    _ops = tuple(i.opname for i in _m[_s:_e])
    print(f"_ops (between PUSH_EXC_INFO and RERAISE): {_ops}")

# Check block 84 (the finally copy candidate)
copy_block = cfg.get_block_by_offset(84)
print(f"\nCopy candidate block @{copy_block.start_offset}:")
for instr in copy_block.instructions:
    print(f"  {instr.offset:4d} {instr.opname:30s} {instr.argval}")

_m2 = [i for i in copy_block.instructions if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
_ops2 = tuple(i.opname for i in _m2)
print(f"Copy block ops: {_ops2}")

# Check if _ops2 contains _ops as a subsequence
if _ops and len(_ops) >= 2:
    found = False
    for _mi in range(len(_ops2) - len(_ops) + 1):
        if _ops2[_mi:_mi + len(_ops)] == _ops:
            found = True
            print(f"Match found at index {_mi}!")
            break
    if not found:
        print(f"No match! _ops={_ops}, _ops2={_ops2}")
        print(f"Looking for {_ops} in {_ops2}")

# Also check block 122
copy_block2 = cfg.get_block_by_offset(122)
print(f"\nCopy candidate block @{copy_block2.start_offset}:")
_m3 = [i for i in copy_block2.instructions if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
_ops3 = tuple(i.opname for i in _m3)
print(f"Copy block2 ops: {_ops3}")
if _ops and len(_ops) >= 2:
    found = False
    for _mi in range(len(_ops3) - len(_ops) + 1):
        if _ops3[_mi:_mi + len(_ops)] == _ops:
            found = True
            print(f"Match found at index {_mi}!")
            break
    if not found:
        print(f"No match for block 122!")
