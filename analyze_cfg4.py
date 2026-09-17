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

# Print all IfRegions with their key attributes
for r in regions:
    if isinstance(r, IfRegion):
        entry_off = r.entry.start_offset if r.entry else -1
        cond_off = r.condition_block.start_offset if r.condition_block else -1
        merge_off = r.merge_block.start_offset if r.merge_block else -1
        then_count = len(r.then_blocks) if r.then_blocks else 0
        else_count = len(r.else_blocks) if r.else_blocks else 0
        print(f"IfRegion: entry={entry_off} cond={cond_off} merge={merge_off} then={then_count} else={else_count} type={r.region_type.name}")
