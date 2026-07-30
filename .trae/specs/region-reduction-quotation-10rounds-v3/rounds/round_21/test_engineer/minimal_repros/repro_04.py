"""repro_04: BUILD_CONST_KEY_MAP 消费模式 — 链式三元共享 merge_block。

测试 aspect: 前驱三元表达式的 merge_block 同时是后继三元表达式的 entry。即第一个三元
的 else 汇合点直接进入第二个三元的条件测试。两个三元最终都流入 BUILD_CONST_KEY_MAP
消费。违反原则 2（每块唯一归属）：merge_block 同时是前驱的 merge 和后继的 entry，
前驱不应独占标记为 generated，否则后继三元 entry 被跳过导致 dict 值丢失。

对应 get_str_data 根因 C：TernaryRegion@844.merge_block == TernaryRegion@1226.entry。

    d = {'a': x if c1 else y, 'b': z if (x if c1 else y) else 0}
"""


def f(x, y, z, c1):
    a = x if c1 else y
    d = {
        'a': a,
        'b': z if a else 0,
    }
    return d
