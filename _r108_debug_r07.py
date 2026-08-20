"""Debug repro_r2_07 region analysis"""
import sys, dis, marshal, types
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

if not func_code:
    print("Function not found!")
    sys.exit(1)

cfg = build_cfg(func_code)

ra = RegionAnalyzer(cfg)
ra.analyze()

print('=== Regions ===')
for r in ra.regions:
    print(f'{type(r).__name__}: entry={r.entry.start_offset}, blocks={[b.start_offset for b in r.blocks]}')
    if hasattr(r, 'has_finally'):
        print(f'  has_finally={r.has_finally}, has_else={r.has_else}')
        print(f'  try_blocks={[b.start_offset for b in r.try_blocks]}')
        print(f'  except_handlers={[(et, en, [b.start_offset for b in hbs]) for et, en, hbs in r.except_handlers]}')
        print(f'  finally_blocks={[b.start_offset for b in r.finally_blocks]}')
        print(f'  finally_copy_blocks={getattr(r, "finally_copy_blocks", None)}')
        print(f'  else_blocks={[b.start_offset for b in r.else_blocks] if r.else_blocks else None}')
    if hasattr(r, 'handler_entry_blocks'):
        print(f'  handler_entry_blocks={[b.start_offset for b in r.handler_entry_blocks]}')

print()
print('=== Block to Region ===')
for blk, r in ra.block_to_region.items():
    print(f'  block {blk.start_offset} -> {type(r).__name__}(entry={r.entry.start_offset})')

print()
print('=== CFG Blocks ===')
# cfg.blocks might be a dict with int keys
if hasattr(cfg, 'blocks') and isinstance(cfg.blocks, dict):
    for offset in sorted(cfg.blocks.keys()):
        b = cfg.blocks[offset]
        print(f'  block {offset}: {[(i.opname, i.argval) for i in b.instructions]}')
        print(f'    successors: {[s.start_offset for s in b.successors]}')
else:
    # Try iterating block objects directly
    blocks_list = list(cfg.blocks) if not isinstance(cfg.blocks, dict) else list(cfg.blocks.values())
    for b in sorted(blocks_list, key=lambda x: x.start_offset):
        print(f'  block {b.start_offset}: {[(i.opname, i.argval) for i in b.instructions]}')
        print(f'    successors: {[s.start_offset for s in b.successors]}')
