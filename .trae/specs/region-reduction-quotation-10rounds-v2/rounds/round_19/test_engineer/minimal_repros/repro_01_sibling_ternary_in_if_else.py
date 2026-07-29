"""repro_01: 根因 B 核心 — IfRegion else_blocks 中的兄弟 TernaryRegion。

模拟 get_str_data 的 IfRegion@614 结构：循环体内 if not datas: continue，
else 分支包含兄弟 TernaryRegion（parent 是外层 LoopRegion，非 IfRegion）。
_process_if_blocks 仅从 region.children 收集，遗漏 else_blocks 中的兄弟三元。

违反原则 3（嵌套即抽象节点）+ 原则 4（入口引用语义）。
"""


def f(items):
    result = {}
    i = 0
    for item in items:
        if not item:
            continue
        else:
            result[i] = item if item > 0 else -item
        i += 1
    return result
