import sys, marshal, types
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

# Find the IfRegion with entry=816 (if self._price_limit:)
for r in regions:
    if isinstance(r, IfRegion) and r.entry and r.entry.start_offset == 816:
        print("IfRegion entry=816 (if self._price_limit:)")
        print(f"  region_type: {r.region_type}")
        print(f"  condition_block: {r.condition_block.start_offset if r.condition_block else None}")
        print(f"  merge_block: {r.merge_block.start_offset if r.merge_block else None}")
        print(f"  then_blocks: {[b.start_offset for b in r.then_blocks]}")
        print(f"  else_blocks: {[b.start_offset for b in r.else_blocks]}")
        print(f"  blocks: {[b.start_offset for b in r.blocks]}")
        print(f"  children: {[(type(c).__name__, c.entry.start_offset if c.entry else None) for c in (r.children or [])]}")
        break

# Also check what happens with block_to_region for specific blocks
print("\nblock_to_region for key blocks:")
for offset in [1068, 1194, 1236, 1320, 1324, 1372, 1696, 1834, 1884, 2164, 2208, 2464, 2468, 3210, 3226, 3954]:
    block = cfg.get_block_by_offset(offset)
    if block:
        owner = analyzer.block_to_region.get(block)
        if owner:
            print(f"  offset {offset}: owned by {type(owner).__name__} entry={owner.entry.start_offset if owner.entry else None}")
        else:
            print(f"  offset {offset}: no owner")

# Check the IfRegion for entry=1068 (BUY check inside price_limit)
for r in regions:
    if isinstance(r, IfRegion) and r.entry and r.entry.start_offset == 1068:
        print("\nIfRegion entry=1068 (BUY check inside price_limit)")
        print(f"  region_type: {r.region_type}")
        print(f"  condition_block: {r.condition_block.start_offset if r.condition_block else None}")
        print(f"  merge_block: {r.merge_block.start_offset if r.merge_block else None}")
        print(f"  then_blocks: {[b.start_offset for b in r.then_blocks]}")
        print(f"  else_blocks: {[b.start_offset for b in r.else_blocks]}")
        print(f"  parent: {type(r.parent).__name__ if r.parent else None} entry={r.parent.entry.start_offset if r.parent and r.parent.entry else None}")
        break
