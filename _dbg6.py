import sys; sys.path.insert(0, '.')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, BoolOpRegion

src = 'x = a and b'
code = compile(src, '<test>', 'exec')
cfg = CFGBuilder().build(code)
analyzer = RegionAnalyzer(cfg)
regions = analyzer.analyze()

print(f"Total regions: {len(regions)}")
for r in regions:
    print(f"  {type(r).__name__}: entry={r.entry.start_offset if r.entry else None}")
    if isinstance(r, BoolOpRegion):
        chain_info = [(b.start_offset, op) for b, op in r.op_chain]
        print(f"    chain={chain_info}, merge={r.merge_block.start_offset if r.merge_block else None}")
        print(f"    value_target={r.value_target}")
