import sys, marshal, types
sys.path.insert(0, 'F:/Downloads/pythoncdc-main')
from core.cfg import build_cfg
from core.cfg.dominator_analyzer import DominatorAnalyzer
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

# Monkey-patch to trace merge computation
original_compute = RegionAnalyzer._compute_merge_from_jump_targets
original_ncpd = RegionAnalyzer._find_nearest_common_post_dominator
original_loop_merge = RegionAnalyzer._compute_in_loop_if_merge

def traced_compute(self, header, then_succ, else_succ):
    result = original_compute(self, header, then_succ, else_succ)
    if header.start_offset == 816:
        print(f"  _compute_merge_from_jump_targets(header=816, then={then_succ.start_offset}, else={else_succ.start_offset}) = {result.start_offset if result else None}")
    return result

def traced_ncpd(self, blocks):
    result = original_ncpd(self, blocks)
    block_offsets = {b.start_offset for b in blocks}
    if 1068 in block_offsets or 1324 in block_offsets:
        print(f"  _find_nearest_common_post_dominator({block_offsets}) = {result.start_offset if result else None}")
    return result

def traced_loop_merge(self, then_succ, else_succ, loop_region, exclude):
    result = original_loop_merge(self, then_succ, else_succ, loop_region, exclude)
    if then_succ.start_offset == 1068 or else_succ.start_offset == 1324:
        print(f"  _compute_in_loop_if_merge(then={then_succ.start_offset}, else={else_succ.start_offset}) = {result.start_offset if result else None}")
    return result

RegionAnalyzer._compute_merge_from_jump_targets = traced_compute
RegionAnalyzer.find_nearest_common_post_dominator = traced_ncpd
RegionAnalyzer._compute_in_loop_if_merge = traced_loop_merge

analyzer = RegionAnalyzer(cfg)
regions = analyzer.analyze()

# Find the IfRegion with entry=816
for r in regions:
    if isinstance(r, IfRegion) and r.entry and r.entry.start_offset == 816:
        print(f"\nFinal IfRegion entry=816: merge={r.merge_block.start_offset if r.merge_block else None}")
        print(f"  then={[b.start_offset for b in r.then_blocks]}")
        print(f"  else={[b.start_offset for b in r.else_blocks]}")
