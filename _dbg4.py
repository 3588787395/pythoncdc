import sys; sys.path.insert(0, '.')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, BoolOpRegion, IfRegion
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.code_generator import CodeGenerator

src = 'if a and b:\n    x = 1'
code = compile(src, '<test>', 'exec')
cfg = CFGBuilder().build(code)
analyzer = RegionAnalyzer(cfg)
regions = analyzer.analyze()

if_region = None
boolop_region = None
for r in regions:
    if isinstance(r, IfRegion) and r.parent is None:
        if_region = r
    if isinstance(r, BoolOpRegion):
        boolop_region = r

cond_block = if_region.condition_block
print(f"cond_block offset: {cond_block.start_offset}")
region_for_cond = analyzer.get_region_for_block(cond_block)
print(f"get_region_for_block({cond_block.start_offset}): {type(region_for_cond).__name__ if region_for_cond else None}")

desc_boolop = if_region.find_descendant_region_for_block(cond_block, (BoolOpRegion,))
print(f"find_descendant: {type(desc_boolop).__name__ if desc_boolop else None}")

print(f"boolop_region: entry={boolop_region.entry.start_offset if boolop_region else None}")
print(f"boolop_region condition_expr: {getattr(boolop_region, 'condition_expr', None) if boolop_region else None}")

# Check block_to_region mapping
for block in cfg.get_blocks_in_order():
    r = analyzer.block_to_region.get(block)
    print(f"  block {block.start_offset}: {type(r).__name__ if r else None}")
