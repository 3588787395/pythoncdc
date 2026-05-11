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
    elif isinstance(r, IfRegion):
        cond_info = f"cond_block={r.condition_block.start_offset}" if r.condition_block else "no cond"
        print(f"  IfRegion: entry={r.entry.start_offset}, {cond_info}, {parent_info}")
        if hasattr(r, 'children') and r.children:
            for c in r.children:
                print(f"    child: {type(c).__name__}@{c.entry.start_offset if c.entry else None}")
    else:
        print(f"  {type(r).__name__}: entry={r.entry.start_offset}, {parent_info}")

# Now check what _generate_boolop sees
from core.cfg.region_ast_generator import RegionASTGenerator
generator = RegionASTGenerator(cfg, analyzer)

# Check the boolop region's enclosing parent
for r in regions:
    if isinstance(r, BoolOpRegion):
        enclosing = r.find_enclosing_parent((type(None), type(None)))
        print(f"\nBoolOpRegion enclosing parent search:")
        # Manually check
        current = r.parent
        while current:
            print(f"  parent: {type(current).__name__}@{current.entry.start_offset if current.entry else None}")
            if hasattr(current, 'condition_block') and current.condition_block:
                print(f"    condition_block: {current.condition_block.start_offset}")
            current = current.parent if hasattr(current, 'parent') else None
