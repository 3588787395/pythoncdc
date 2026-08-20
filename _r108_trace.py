"""Debug _generate_try for repro_r2_07 - trace post-try block collection"""
import sys, marshal, types, json
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

# Find the TryExceptRegion
try_region = None
for r in ra.regions:
    if hasattr(r, 'has_finally'):
        try_region = r
        break

print(f"TryExceptRegion entry={try_region.entry.start_offset}")
print(f"  blocks={[b.start_offset for b in try_region.blocks]}")
print(f"  finally_copy_blocks={try_region.finally_copy_blocks}")

# Manually check what the fix would do
_try_off_set = set(b.start_offset for b in try_region.try_blocks)
_else_off_set = set(b.start_offset for b in try_region.else_blocks) if try_region.else_blocks else set()
_fin_off_set = set(b.start_offset for b in try_region.finally_blocks)
_h_off_set = set()
for _et, _en, _hbs in try_region.except_handlers:
    for _hb in _hbs:
        _h_off_set.add(_hb.start_offset)
_fc_key_set = set(try_region.finally_copy_blocks.keys())
_known_struct = _try_off_set | _else_off_set | _fin_off_set | _h_off_set | _fc_key_set

print(f"\n  _try_off_set={_try_off_set}")
print(f"  _else_off_set={_else_off_set}")
print(f"  _fin_off_set={_fin_off_set}")
print(f"  _h_off_set={_h_off_set}")
print(f"  _fc_key_set={_fc_key_set}")
print(f"  _known_struct={_known_struct}")

# Check finally_copy_blocks successors
for fc_offset in _fc_key_set:
    fc_block = cfg.get_block_by_offset(fc_offset)
    if fc_block:
        for succ in fc_block.successors:
            print(f"\n  fc block {fc_offset} -> succ {succ.start_offset}")
            print(f"    succ.start_offset in _known_struct: {succ.start_offset in _known_struct}")
            print(f"    succ in block_to_region: {succ in ra.block_to_region}")

# Now try generating
gen = RegionASTGenerator(cfg, ra)
result = gen._generate_try(try_region)
print(f"\nGenerated AST: {json.dumps(result, indent=2, default=str)[:2000]}")
print(f"\nGenerated blocks: {[b.start_offset for b in gen.generated_blocks if hasattr(b, 'start_offset')]}")
