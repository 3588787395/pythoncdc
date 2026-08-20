import sys
sys.path.insert(0, '.')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, BlockRole
import marshal

path = '.trae/specs/decompiler-test-comprehensive-10rounds/rounds/round_02/test_engineer/minimal_repros/repro_r2_10_try_wrap_for_else_break.pyc'
with open(path, 'rb') as f:
    f.read(4); f.read(4); f.read(8)
    code = marshal.load(f)

func_code = code.co_consts[1]
cfg_builder = CFGBuilder()
cfg = cfg_builder.build(func_code)

region_analyzer = RegionAnalyzer(cfg)
regions = region_analyzer.analyze()

# Print all regions
for region in regions:
    print(f'Region: {type(region).__name__}')
    if hasattr(region, 'region_type'):
        print(f'  region_type: {region.region_type}')
    if hasattr(region, 'try_blocks'):
        print(f'  try_blocks: {[b.id for b in region.try_blocks]}')
    if hasattr(region, 'handler_entry_blocks'):
        print(f'  handler_entry_blocks: {[b.id for b in region.handler_entry_blocks]}')
    if hasattr(region, 'except_handlers'):
        for i, h in enumerate(region.except_handlers):
            if isinstance(h, dict):
                print(f'  except_handler[{i}]: {h}')
            elif isinstance(h, tuple):
                print(f'  except_handler[{i}]: {h}')
            else:
                print(f'  except_handler[{i}]: {type(h).__name__} {h}')
    if hasattr(region, 'else_blocks'):
        print(f'  else_blocks: {[b.id for b in region.else_blocks]}')
    if hasattr(region, 'finally_blocks'):
        print(f'  finally_blocks: {[b.id for b in region.finally_blocks]}')
    if hasattr(region, 'body_blocks'):
        print(f'  body_blocks: {[b.id for b in region.body_blocks]}')
    if hasattr(region, 'entry'):
        print(f'  entry: block {region.entry.id}')

# Print all blocks
print('\n=== Blocks ===')
for offset, block in sorted(cfg.blocks.items()):
    instrs = [(i.opname, i.arg) for i in block.instructions]
    print(f'  Block {block.id} (offset {block.start_offset}): {instrs}')
