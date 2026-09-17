import sys, marshal, types
sys.path.insert(0, 'F:/Downloads/pythoncdc-main')
from core.cfg import build_cfg
from core.cfg.dominator_analyzer import DominatorAnalyzer
from core.cfg.region_analyzer import RegionAnalyzer

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

# Check what _get_jump_forward_target returns for blocks 1068 and 1324
block_1068 = cfg.get_block_by_offset(1068)
block_1324 = cfg.get_block_by_offset(1324)

analyzer = RegionAnalyzer(cfg)

for b in [block_1068, block_1324]:
    last = b.get_last_instruction()
    print(f"Block {b.start_offset}: last_instr={last.opname} argval={last.argval}")
    jf_target = analyzer._get_jump_forward_target(b)
    print(f"  JUMP_FORWARD target: {jf_target.start_offset if jf_target else None}")

# Now check _find_jump_forward_in_successors with max_depth=3
print("\n_find_jump_forward_in_successors for block 1068:")
jf_in_succ = analyzer._find_jump_forward_in_successors(block_1068, {block_1068, block_1324, cfg.get_block_by_offset(816)}, max_depth=3)
for t in jf_in_succ:
    print(f"  target: {t.start_offset}")

print("\n_find_jump_forward_in_successors for block 1324:")
jf_in_succ = analyzer._find_jump_forward_in_successors(block_1324, {block_1068, block_1324, cfg.get_block_by_offset(816)}, max_depth=3)
for t in jf_in_succ:
    print(f"  target: {t.start_offset}")

# Also check _is_reachable_bfs from 1324 to block 2464
block_2464 = cfg.get_block_by_offset(2464)
reachable = analyzer._is_reachable_bfs(block_1324, block_2464, {block_1068, block_1324, cfg.get_block_by_offset(816)})
print(f"\n_is_reachable_bfs from 1324 to 2464: {reachable}")

reachable2 = analyzer._is_reachable_bfs(block_1068, block_2464, {block_1068, block_1324, cfg.get_block_by_offset(816)})
print(f"_is_reachable_bfs from 1068 to 2464: {reachable2}")
