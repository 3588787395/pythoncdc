import sys, marshal, types
sys.path.insert(0, 'F:/Downloads/pythoncdc-main')
from core.cfg import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer, IfRegion, LoopRegion

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

# Monkey-patch _find_nearest_common_post_dominator to trace for our specific blocks
original_ncpd = RegionAnalyzer._find_nearest_common_post_dominator

def traced_ncpd(self, *args):
    result = original_ncpd(self, *args)
    block_offsets = {b.start_offset for b in args}
    if 1068 in block_offsets and 1324 in block_offsets:
        import traceback
        print(f"\n  _find_ncpd({{1068, 1324}}) = {result.start_offset if result else None}")
        tb = traceback.format_stack()
        for line in tb[-5:-1]:
            print(f"    {line.strip()}")
    return result

RegionAnalyzer._find_nearest_common_post_dominator = traced_ncpd

analyzer = RegionAnalyzer(cfg)
regions = analyzer.analyze()
