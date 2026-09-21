# -*- coding: utf-8 -*-
# R22 残留 23 —— `A and B or C`（末析取支是单操作数）：两世界同形异因缺陷。
#
# base 与 after 都是 seq_len orig=11 decomp=13（+2，过量发射族，Round 24+ 目标池），
# J2' 不碰它。登记在此防止被"顺带修好"或恶化而无人知晓。
# 类别 RESIDUE（两世界都 MISMATCH，不计失败）。
def f(a, b, c):
    if a and b or c:
        return 1
    return 0
