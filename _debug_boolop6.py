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

for r in regions:
    if isinstance(r, BoolOpRegion):
        print(f"BoolOpRegion: entry={r.entry.start_offset}")
        print(f"  blocks: {[b.start_offset for b in r.blocks]}")
        print(f"  merge: {r.merge_block.start_offset if r.merge_block else None}")
        print(f"  is_condition_context: {getattr(r, 'is_condition_context', None)}")
        print(f"  parent: {type(r.parent).__name__ if r.parent else None}")
    elif isinstance(r, IfRegion):
        print(f"IfRegion: entry={r.entry.start_offset}")
        print(f"  blocks: {[b.start_offset for b in r.blocks]}")
        print(f"  condition_block: {r.condition_block.start_offset if r.condition_block else None}")
        print(f"  then_blocks: {[b.start_offset for b in r.then_blocks]}")
        print(f"  else_blocks: {[b.start_offset for b in r.else_blocks]}")
        print(f"  children: {[(type(c).__name__, c.entry.start_offset) for c in r.children] if r.children else []}")
