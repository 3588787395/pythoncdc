"""repro_06: 三元 merge_block 是后继三元 entry（链式共享）。

模拟 TernaryRegion@844.merge_block=1226 == TernaryRegion@1226.entry。
前驱三元生成时标记 merge_block=1226 为 generated，
后继三元的 entry=1226 已 generated 被跳过。
"""


def f(cond, x, y):
    a = x if cond else 0
    b = y if cond else 0
    return {'a': a, 'b': b}
