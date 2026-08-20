import sys
sys.path.insert(0, '.')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer
from core.cfg.region_ast_generator import RegionASTGenerator
import marshal

path = '.trae/specs/decompiler-test-comprehensive-10rounds/rounds/round_02/test_engineer/minimal_repros/repro_r2_07_finally_implicit_return.pyc'
with open(path, 'rb') as f:
    f.read(4); f.read(4); f.read(8)
    code = marshal.load(f)

func_code = code.co_consts[1]
cfg_builder = CFGBuilder()
cfg = cfg_builder.build(func_code)

region_analyzer = RegionAnalyzer(cfg)
regions = region_analyzer.analyze()

# Print regions
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
    if hasattr(region, 'handler_entry_blocks'):
        print(f'  handler_entry_blocks: {[b.id for b in region.handler_entry_blocks]}')
    if hasattr(region, 'has_else'):
        print(f'  has_else: {region.has_else}')
    if hasattr(region, 'has_finally'):
        print(f'  has_finally: {region.has_finally}')
    if hasattr(region, 'entry'):
        print(f'  entry: block {region.entry.id}')

# Print blocks
print('\n=== Blocks ===')
for offset, block in sorted(cfg.blocks.items()):
    instrs = [(i.opname, i.arg, getattr(i, 'argval', None)) for i in block.instructions]
    print(f'  Block {block.id} (offset {block.start_offset}): {instrs}')

# Generate AST
ast_gen = RegionASTGenerator(cfg, region_analyzer, regions)
ast = ast_gen.generate()
print(f'\nFinal AST body: {ast.get("body")}')
