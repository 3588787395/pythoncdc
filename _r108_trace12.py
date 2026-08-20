"""Check block 128 and 20 instructions"""
import sys, marshal
sys.path.insert(0, '.')
from core.cfg.cfg_builder import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer

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

# Check block at offset 18's successors
for offset in [18, 20, 128]:
    b = cfg.get_block_by_offset(offset)
    if b:
        print(f"Block {offset}: {[(i.opname, i.argval) for i in b.instructions]}")
        print(f"  successors: {[s.start_offset for s in b.successors]}")
    else:
        print(f"Block {offset}: NOT FOUND")

# Also check: does _generate_block_statements(block 18) return Expr?
from core.cfg.region_ast_generator import RegionASTGenerator
gen = RegionASTGenerator(cfg)
gen.regions = gen.region_analyzer.analyze()

block_18 = cfg.get_block_by_offset(18)
ebs = gen._generate_block_statements(block_18)
print(f"\n_generate_block_statements(block 18): {ebs}")
