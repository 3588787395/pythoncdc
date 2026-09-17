import sys, marshal, types, dis
sys.path.insert(0, 'F:/Downloads/pythoncdc-main')
from core.cfg import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer, IfRegion, LoopRegion, RegionType

pyc = 'F:/Downloads/pythoncdc-main/site-packages/IQEngine/plugins/plugin_system_matcher/matcher.pyc'
with open(pyc, 'rb') as f:
    f.read(16); orig = marshal.load(f)

def extract(co):
    r = {}; r[co.co_name or '<module>'] = co
    for c in co.co_consts:
        if isinstance(c, types.CodeType): r.update(extract(c))
    return r

om = extract(orig)
match_co = om['match']

cfg = build_cfg(match_co)
analyzer = RegionAnalyzer(cfg)
regions = analyzer.analyze()

# Check the IfRegion with entry=800 (if self._price_limit)
for r in regions:
    if isinstance(r, IfRegion) and r.entry and r.entry.start_offset == 800:
        print("IfRegion entry=800 (if self._price_limit:)")
        print(f"  region_type: {r.region_type}")
        print(f"  condition_block: {r.condition_block.start_offset if r.condition_block else None}")
        print(f"  merge_block: {r.merge_block.start_offset if r.merge_block else None}")
        then_then = set(b.start_offset for b in r.then_blocks)
        then_else = set(b.start_offset for b in r.else_blocks)
        overlap = then_then & then_else
        print(f"  then_blocks count: {len(r.then_blocks)}")
        print(f"  else_blocks count: {len(r.else_blocks)}")
        print(f"  overlap count: {len(overlap)}")
        if overlap:
            print(f"  overlap offsets: {sorted(overlap)}")
        # Check which blocks in else_blocks are NOT in then_blocks
        else_only = then_else - then_then
        print(f"  else_only offsets: {sorted(else_only)}")
        break

# Check the LoopRegion
for r in regions:
    if isinstance(r, LoopRegion) and r.entry and r.entry.start_offset == 6:
        print("\nLoopRegion entry=6 (for loop)")
        print(f"  region_type: {r.region_type}")
        print(f"  body_blocks count: {len(r.body_blocks) if r.body_blocks else 0}")
        if r.body_blocks:
            print(f"  body_blocks offsets: {[b.start_offset for b in r.body_blocks]}")
        break
