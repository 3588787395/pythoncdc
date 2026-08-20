"""Debug else block generation for repro_r2_07"""
import sys, marshal
sys.path.insert(0, '.')
from core.cfg.cfg_builder import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer
from core.cfg.region_ast_generator import RegionASTGenerator

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
ra = RegionAnalyzer(cfg)
ra.analyze()

# Find block 18 (else block)
for offset in sorted(cfg.blocks.keys()):
    b = cfg.blocks[offset]
    if b.start_offset == 18:
        print(f"Block 18 instructions: {[(i.opname, i.argval) for i in b.instructions]}")
        print(f"Block 18 successors: {[s.start_offset for s in b.successors]}")
        break

# Find block 20 (finally normal path)
for offset in sorted(cfg.blocks.keys()):
    b = cfg.blocks[offset]
    if b.start_offset == 20:
        print(f"Block 20 instructions: {[(i.opname, i.argval) for i in b.instructions]}")
        print(f"Block 20 successors: {[s.start_offset for s in b.successors]}")
        break

# Check block roles
for r in ra.regions:
    if hasattr(r, 'has_finally'):
        for eb in r.else_blocks:
            role = ra.get_block_role(eb)
            print(f"else block {eb.start_offset} role: {role}")
        for fb in r.finally_blocks:
            role = ra.get_block_role(fb)
            print(f"finally block {fb.start_offset} role: {role}")

# Check finally_copy_blocks
for r in ra.regions:
    if hasattr(r, 'has_finally'):
        print(f"finally_copy_blocks: {r.finally_copy_blocks}")
        # block 20 is the finally normal path
        # Check if it's in finally_copy_blocks values
        for fc_offset, fc_keep in r.finally_copy_blocks.items():
            print(f"  fc {fc_offset} -> keep {fc_keep}")
