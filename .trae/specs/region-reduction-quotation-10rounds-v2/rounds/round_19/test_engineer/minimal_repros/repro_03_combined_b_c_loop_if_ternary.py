"""repro_03: 根因 B+C 组合 — 循环内 IfRegion else 中的链式三元。

模拟 get_str_data 核心结构：
- LoopRegion 包含 IfRegion（if not datas: continue）
- IfRegion 的 else_blocks 包含 2 个兄弟 TernaryRegion
- TernaryRegion@A.merge_block == TernaryRegion@B.entry（链式共享）
- TernaryRegion@B.merge_block 含 BUILD_CONST_KEY_MAP + STORE_SUBSCR
"""


def f(stocks, n):
    order = {}
    for stock in stocks:
        if n <= 0:
            continue
        else:
            cond = n % 2
            order[stock] = {
                'a': cond if cond == 1 else 0,
                'b': cond if cond == 1 else 0,
            }
    return order
