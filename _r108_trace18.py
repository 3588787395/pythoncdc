"""Check all block successors"""
import sys, marshal
sys.path.insert(0, '.')
from core.cfg.cfg_builder import build_cfg

pyc_path = '.trae/specs/decompiler-test-comprehensive-10rounds/rounds/round_02/test_engineer/minimal_repros/repro_r2_07_finally_implicit_return.pyc'
with open(pyc_path, 'rb') as f:
    f.read(16)
    code = marshal.load(f)

func_code = None
for c in code.co_consts:
    if hasattr(c, 'co_name') and c.co_name == 'test_finally_implicit_return':
        func_code = c
        break

cfg = build_cfg(func_code)

# Check else_blocks successors chain
else_block = cfg.get_block_by_offset(18)
print(f"else block 18 successors: {[s.start_offset for s in else_block.successors]}")

for succ in else_block.successors:
    print(f"  succ {succ.start_offset}: {[(i.opname, i.argval) for i in succ.instructions]}")
    print(f"    successors: {[s.start_offset for s in succ.successors]}")
    for s2 in succ.successors:
        print(f"    s2 {s2.start_offset}: {[(i.opname, i.argval) for i in s2.instructions]}")
        print(f"      successors: {[s.start_offset for s in s2.successors]}")
