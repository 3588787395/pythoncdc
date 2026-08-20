import sys
sys.path.insert(0, '.')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer
import marshal

path = '.trae/specs/decompiler-test-comprehensive-10rounds/rounds/round_02/test_engineer/minimal_repros/repro_r2_12_try_finally_pass.pyc'
with open(path, 'rb') as f:
    f.read(4); f.read(4); f.read(8)
    code = marshal.load(f)

func_code = code.co_consts[1]
cfg_builder = CFGBuilder()
cfg = cfg_builder.build(func_code)

region_analyzer = RegionAnalyzer(cfg)
regions = region_analyzer.analyze()
region_analyzer._annotate_all_roles(region_analyzer.regions)

# Print blocks with roles
print("=== Blocks ===")
for offset, block in sorted(cfg.blocks.items()):
    role = region_analyzer.get_block_role(block)
    instrs = [(i.opname, i.arg) for i in block.instructions]
    print(f'  Block {block.id} (offset {block.start_offset}): role={role}, instrs={instrs}')
    print(f'    successors: {[s.id for s in block.successors]}')

# Print regions
print("\n=== Regions ===")
for region in regions:
    print(f'Region: {type(region).__name__}')
    if hasattr(region, 'region_type'):
        print(f'  region_type: {region.region_type}')
    if hasattr(region, 'try_blocks'):
        print(f'  try_blocks: {[b.id for b in region.try_blocks]}')
    if hasattr(region, 'else_blocks'):
        print(f'  else_blocks: {[b.id for b in region.else_blocks]}')
    if hasattr(region, 'finally_blocks'):
        print(f'  finally_blocks: {[b.id for b in region.finally_blocks]}')
    if hasattr(region, 'has_finally'):
        print(f'  has_finally: {region.has_finally}')
    if hasattr(region, 'body_blocks'):
        print(f'  body_blocks: {[b.id for b in region.body_blocks]}')
    if hasattr(region, 'break_blocks'):
        print(f'  break_blocks: {[b.id for b in region.break_blocks]}')
    if hasattr(region, 'entry'):
        print(f'  entry: block {region.entry.id}')
