"""repro_02: get_str_data 根因 C — 链式共享 merge_block 独占标记。

TernaryRegion@844.merge_block == TernaryRegion@1226.entry。前驱三元生成时将
共享 merge_block 标记为 generated，导致后继三元 entry 已在 generated_blocks 中被跳过。

违反原则 2（每块唯一归属）：merge_block 同时是前驱的 merge 和后继的 entry，
前驱不应独占标记。

后续迭代建议：标记 child.blocks 为 generated 时，检测 merge_block 是否同时是
另一 TernaryRegion 的 entry，若是则不独占标记该共享块。
"""


def f(items):
    result = {}
    for i, item in enumerate(items):
        a = item if item > 0 else -item
        b = a * 2 if a > 1 else a
        result[i] = b
    return result
