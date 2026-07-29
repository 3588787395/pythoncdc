"""repro_08: 循环内 IfRegion + 兄弟三元（parent=LoopRegion）。

完整模拟 get_str_data 的 LoopRegion@610 → IfRegion@614 结构。
IfRegion@614 的 else_blocks 包含 TernaryRegion@844/@1226 的 entry，
但两者的 parent 是 LoopRegion@610（非 IfRegion@614）。
_process_if_blocks 遍历 IfRegion@614.children（为空）时遗漏兄弟三元。
"""


def f(items):
    result = {}
    for item in items:
        if not item:
            continue
        else:
            x = item if item > 0 else 0
            y = item if item > 1 else 1
            result[item] = (x, y)
    return result
