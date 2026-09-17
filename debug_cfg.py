import sys, marshal, types
sys.path.insert(0, '.')
pyc = 'site-packages/IQEngine/plugins/plugin_system_matcher/matcher.pyc'
with open(pyc, 'rb') as f:
    f.read(16); orig = marshal.load(f)

def extract(co):
    r = {}; r[co.co_name] = co
    for c in co.co_consts:
        if isinstance(c, type(orig)):
            r.update(extract(c))
    return r

om = extract(orig)
co = om['match']

from core.cfg.cfg_builder import build_cfg
from core.cfg.dominator_analyzer import DominatorAnalyzer
from core.cfg.region_analyzer import RegionAnalyzer, IfRegion, LoopRegion, BoolOpRegion

cfg = build_cfg(co)
dom = DominatorAnalyzer(cfg)
ra = RegionAnalyzer(cfg, dom)
ra.analyze()

# The mismatch is in the match function - 544 true_diffs
# Show the IfRegions and their structure around the mismatch area
print('IfRegions with large else blocks:')
for r in ra.regions:
    if isinstance(r, IfRegion) and r.entry and 1000 <= r.entry.start_offset <= 1400:
        entry = f'B{r.entry.start_offset}'
        cond = f'B{r.condition_block.start_offset}' if r.condition_block else 'None'
        then_cnt = len(r.then_blocks)
        else_cnt = len(r.else_blocks)
        print(f'  entry={entry} cond={cond} then={then_cnt} else={else_cnt} type={r.region_type}')
