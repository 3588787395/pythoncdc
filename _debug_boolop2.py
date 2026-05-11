import sys, os
sys.path.insert(0, '.')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, BoolOpRegion, IfRegion

src = 'if a and b:\n    x = 1'
code = compile(src, '<test>', 'exec')
cfg_builder = CFGBuilder()
cfg = cfg_builder.build(code)
analyzer = RegionAnalyzer(cfg)
regions = analyzer.analyze()

print("=== Regions ===")
for r in regions:
    parent_info = f"parent={type(r.parent).__name__}@{r.parent.entry.start_offset}" if r.parent else "no parent"
    if isinstance(r, BoolOpRegion):
        chain_info = [(b.start_offset, op) for b, op in r.op_chain]
        print(f"  BoolOpRegion: entry={r.entry.start_offset}, chain={chain_info}, merge={r.merge_block.start_offset if r.merge_block else None}, {parent_info}")
        if hasattr(r, 'is_condition_context'):
            print(f"    is_condition_context={r.is_condition_context}")
        if hasattr(r, 'condition_expr'):
            print(f"    condition_expr={r.condition_expr}")
    elif isinstance(r, IfRegion):
        print(f"  IfRegion: entry={r.entry.start_offset}, cond={r.condition_block.start_offset if r.condition_block else None}, {parent_info}")
        if hasattr(r, 'children') and r.children:
            for c in r.children:
                print(f"    child: {type(c).__name__}@{c.entry.start_offset if c.entry else None}")
    else:
        print(f"  {type(r).__name__}: entry={r.entry.start_offset}, {parent_info}")

print()
print("=== Block to Region ===")
for block in cfg.get_blocks_in_order():
    region = analyzer.get_region_for_block(block)
    if region:
        print(f"  block {block.start_offset}: {type(region).__name__}@{region.entry.start_offset if region.entry else None}")
