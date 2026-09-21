# -*- coding: utf-8 -*-
# R22 负对照 06 —— 塌缩合法的场景：if 在 for 内、汇点臂 return、else_succ 同一循环。
#
# then 臂入口与 else_succ 的最内层 enclosing loop 都是这个 for → (a) 不拦；
# 臂内是 `return x`（非裸 return None）→ (b) 不拦；塌缩本来就该发生。
# J1' 落地后必须**继续**发生塌缩，产物仍逐指令一致。
# 本复现（<module>.f，orig=15）：base=MATCH after=MATCH。类别 GUARD。
def f(xs, y):
    for x in xs:
        if y:
            return x
    return y
