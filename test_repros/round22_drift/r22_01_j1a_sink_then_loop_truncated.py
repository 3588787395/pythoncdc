# -*- coding: utf-8 -*-
# R22 锚点 01 —— J1'(a) 作用域分裂：汇点臂塌缩把整个 else 侧语句族吞掉。
#
# 规则站点 core/cfg/region_analyzer.py:17132（46e752ab）
#     if not _25b_else_is_cond and self._if_arm_is_sink(then_blocks, then_stop):
#         merge = else_succ                      # R13c 汇点塌缩
# J1'(a) 增加的同层前置条件：_find_enclosing_loop(then_blocks[0]) is
# _find_enclosing_loop(else_succ)，两块的最内层 enclosing loop 必须同一个。
#
# 语料锚点 site-packages/fly/common/flytools.pyc <module>.get_mem_under_oom_status
#   base 核 strict: seq_len orig=47 decomp=18（−29，整段 for 循环 + 赋值被丢）
#   实测该站点（D:/Temp/r22batt/log_ft.txt）：cond@42 then=54 else_succ=58
#   else_succ.successors=?@140[FOR_ITER] same_loop=False shared_rn=False arm_sink=True
#   → else_succ(58) 是 for 循环的循环头块（含 GET_ITER），臂入口 54 不在任何循环内。
#
# 本复现（目标函数 <module>.f，orig=28）：base=MISMATCH decomp=11，after=MATCH。
# 类别 FIX —— J1'(a) 单独修好（mirror/j1a），J1'(b)/J2'/J3' 单独都修不好。
def f(x, ys):
    d = {}
    if x == '':
        return d
    zs = list(ys)
    for z in zs:
        if z:
            d['a'] = 1
            break
    return d
