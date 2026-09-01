"""R29 测试工程师：追踪repro_r29_12的merge计算"""
import sys
sys.path.insert(0, '/workspace')

from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer

SRC = '''def f(x, y, z):
    if x == 1:
        y = 10
    elif x == 2:
        y = 20
    elif x == 3:
        y = 30
    elif x == 4:
        if z:
            return z
        return y
    if y is None:
        return 0
    return y
'''

co = compile(SRC, '<test>', 'exec')
f_co = co.co_consts[0]

builder = CFGBuilder()
cfg = builder.build(f_co)

# 找到各个block
blocks = {b.start_offset: b for b in cfg.get_blocks_in_order()}

# 检查 block 14 和 block 20 的 post-dominator
print("=== Block info ===")
for off in [0, 14, 20, 32, 38, 50, 56, 68, 72, 76, 80, 84, 88]:
    b = blocks[off]
    last = b.get_last_instruction()
    ipd = b.immediate_post_dominator
    ipd_off = ipd.start_offset if ipd else None
    print(f"  blk@{off}: ipd={ipd_off}, succs={[s.start_offset for s in b.successors]}, preds={[p.start_offset for p in b.predecessors]}")

# 创建analyzer并测试_find_nearest_common_post_dominator
analyzer = RegionAnalyzer(cfg)

# 测试 block 0 的 if 检测
print("\n=== Testing merge computation for block@0 ===")
then_succ = blocks[14]  # if x==1: then
else_succ = blocks[20]  # elif x==2: else

ncpd = analyzer._find_nearest_common_post_dominator(then_succ, else_succ)
print(f"  NCPD(14, 20) = {ncpd.start_offset if ncpd else None}")

print(f"  then_succ(14).immediate_post_dominator = {then_succ.immediate_post_dominator.start_offset if then_succ.immediate_post_dominator else None}")
print(f"  else_succ(20).immediate_post_dominator = {else_succ.immediate_post_dominator.start_offset if else_succ.immediate_post_dominator else None}")

_then_sink = any(i.opname in ('RAISE_VARARGS', 'RETURN_VALUE') for i in then_succ.instructions) or then_succ.immediate_post_dominator is None
_else_sink = any(i.opname in ('RAISE_VARARGS', 'RETURN_VALUE') for i in else_succ.instructions) or else_succ.immediate_post_dominator is None
print(f"  _then_sink={_then_sink}, _else_sink={_else_sink}")

# 检查 then_succ 的前驱
print(f"\n  then_succ(14).predecessors = {[p.start_offset for p in then_succ.predecessors]}")
_if_struct = {blocks[0], then_succ, else_succ}
print(f"  _if_struct_blocks = {[b.start_offset for b in _if_struct]}")
_then_has_external = any(p not in _if_struct for p in then_succ.predecessors)
print(f"  _then_has_external_pred = {_then_has_external}")

# 如果 merge = then_succ.immediate_post_dominator
merge = then_succ.immediate_post_dominator
print(f"  merge (then_succ.IPD) = {merge.start_offset if merge else None}")

# 测试 block 38 的 if 检测
print("\n=== Testing merge computation for block@38 ===")
then_succ_38 = blocks[50]  # if x==3: then
else_succ_38 = blocks[56]  # elif x==4: else

ncpd_38 = analyzer._find_nearest_common_post_dominator(then_succ_38, else_succ_38)
print(f"  NCPD(50, 56) = {ncpd_38.start_offset if ncpd_38 else None}")
print(f"  then_succ(50).IPD = {then_succ_38.immediate_post_dominator.start_offset if then_succ_38.immediate_post_dominator else None}")
print(f"  else_succ(56).IPD = {else_succ_38.immediate_post_dominator.start_offset if else_succ_38.immediate_post_dominator else None}")

_then_sink_38 = any(i.opname in ('RAISE_VARARGS', 'RETURN_VALUE') for i in then_succ_38.instructions) or then_succ_38.immediate_post_dominator is None
_else_sink_38 = any(i.opname in ('RAISE_VARARGS', 'RETURN_VALUE') for i in else_succ_38.instructions) or else_succ_38.immediate_post_dominator is None
print(f"  _then_sink={_then_sink_38}, _else_sink={_else_sink_38}")

# 检查 else_succ_38 的前驱（block 56）
print(f"\n  else_succ(56).predecessors = {[p.start_offset for p in else_succ_38.predecessors]}")
