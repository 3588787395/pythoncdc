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

gen = RegionASTGenerator(cfg, analyzer)

# Check what the top-level regions are
top_regions = [r for r in regions if r.parent is None]
print("Top-level regions:")
for r in top_regions:
    print(f"  {type(r).__name__}: entry={r.entry.start_offset if r.entry else None}")

# Check if the IfRegion is being generated
if_region = None
for r in regions:
    if isinstance(r, IfRegion) and r.parent is None:
        if_region = r
        break

if if_region:
    print(f"\nIfRegion: entry={if_region.entry.start_offset}, cond={if_region.condition_block.start_offset}")
    print(f"  then_blocks: {[b.start_offset for b in if_region.then_blocks]}")
    print(f"  else_blocks: {[b.start_offset for b in if_region.else_blocks]}")
    print(f"  children: {[(type(c).__name__, c.entry.start_offset) for c in if_region.children] if if_region.children else []}")

# Check if the BoolOpRegion has condition_expr set
boolop_region = None
for r in regions:
    if isinstance(r, BoolOpRegion):
        boolop_region = r
        break

if boolop_region:
    print(f"\nBoolOpRegion: entry={boolop_region.entry.start_offset}")
    print(f"  is_condition_context: {getattr(boolop_region, 'is_condition_context', None)}")
    print(f"  parent: {type(boolop_region.parent).__name__ if boolop_region.parent else None}")
    _enclosing = boolop_region.find_enclosing_parent((IfRegion, LoopRegion))
    print(f"  enclosing: {type(_enclosing).__name__ if _enclosing else None}")
    if _enclosing and hasattr(_enclosing, 'condition_block'):
        print(f"  enclosing.condition_block: {_enclosing.condition_block.start_offset if _enclosing.condition_block else None}")
        for cb, _ in boolop_region.op_chain:
            if cb == _enclosing.condition_block:
                print(f"  chain block {cb.start_offset} matches enclosing condition_block")
                break
        else:
            print(f"  No chain block matches enclosing condition_block")
