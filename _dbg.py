import sys; sys.path.insert(0, '.')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, BoolOpRegion, IfRegion
src = 'if a and b:\n    x = 1'
code = compile(src, '<test>', 'exec')
cfg = CFGBuilder().build(code)
analyzer = RegionAnalyzer(cfg)
regions = analyzer.analyze()
for r in regions:
    if isinstance(r, BoolOpRegion):
        bl = [b.start_offset for b in r.blocks]
        mg = r.merge_block.start_offset if r.merge_block else None
        ic = getattr(r, 'is_condition_context', None)
        print("BoolOpRegion blocks:", bl, "merge:", mg, "is_cond_ctx:", ic)
    elif isinstance(r, IfRegion):
        bl = [b.start_offset for b in r.blocks]
        cb = r.condition_block.start_offset if r.condition_block else None
        tb = [b.start_offset for b in r.then_blocks]
        eb = [b.start_offset for b in r.else_blocks]
        ch = [(type(c).__name__, c.entry.start_offset) for c in r.children] if r.children else []
        print("IfRegion blocks:", bl, "cond:", cb, "then:", tb, "else:", eb, "children:", ch)
