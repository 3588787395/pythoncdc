"""Check try_blocks successors"""
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

# Check try_blocks successors
for offset in [8, 98, 106, 108]:
    b = cfg.get_block_by_offset(offset)
    if b:
        print(f"try_block {offset}: {[(i.opname, i.argval) for i in b.instructions]}")
        print(f"  successors: {[s.start_offset for s in b.successors]}")
