# -*- coding: utf-8 -*-
# R22 锚点 05 —— J1'(b) 共享隐式 return None（(a) 在此为 True，不起作用）。
#
# 语料锚点 site-packages/IQEngine/plugins/plugin_system_persist/json_persistance.pyc
#   <module>.JsonPersistance.persist  base: seq_len orig=78 decomp=76；after: ok
#   实测站点（D:/Temp/r22batt/logjson）：cond@4 then=26,82,142,164 else_succ=194
#     then_blocks 末块 164 = LOAD_CONST None / RETURN_VALUE   （裸 return None）
#     else_succ=194 = system_log.warning(...) ，其后继 = ?@234[LOAD_CONST RETURN_VALUE]
#     same_loop=True（两块都不在任何循环）shared_rn=True arm_sink=True
#   → 只有 J1'(b) 能禁止这次塌缩；只带 (a) 的 mirror/j1a 上 persist 仍 78→76。
# 本复现把 `with` 换成同层嵌套 if（3.11.9 的 with 会多出 JUMP_FORWARD 桩，
# 反而不触发差异），保持 164/234 两个裸 return None 块的同构关系。
# 本复现（<module>.f，orig=39）：base=MISMATCH decomp=37，after=MATCH。
# 类别 FIX —— **仅 J1'(b) 可修**（mirror/j1a 仍 MISMATCH）。
import sys


def f(d, c):
    try:
        if d != {}:
            if c:
                print(1)
            return None
        sys.stdout.write('empty')
    except BaseException:
        sys.stdout.write('bad')
        return None
