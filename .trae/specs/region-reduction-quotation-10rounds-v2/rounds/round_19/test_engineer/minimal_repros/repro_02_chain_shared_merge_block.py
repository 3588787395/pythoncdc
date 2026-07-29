"""repro_02: 根因 C 核心 — 链式共享 merge_block。

TernaryRegion@A.merge_block == TernaryRegion@B.entry。
前驱 A 生成时标记 merge_block 为 generated，导致后继 B 的 entry 已 generated 被跳过。
违反原则 2（每块唯一归属）。

模拟 volume 三元（@844）→ money 三元（@1226）的链式结构。
"""


def f(cond, a, b, c, d):
    x = a if cond else b
    y = c if cond else d
    return [x, y]
