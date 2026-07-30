"""repro_02: BUILD_CONST_KEY_MAP 消费模式 — 全部 value 为三元表达式。

测试 aspect: 当 dict 所有 value 均为三元表达式时，连续多个 TernaryRegion 的
merge_block 依次流入 BUILD_CONST_KEY_MAP。每个三元的 else 分支与 then 分支都需要
汇合到同一个 dict 构造消费点。反编译器需识别整组三元共享同一消费 (BUILD_CONST_KEY_MAP)，
将其作为单个 dict 构造语句归约。

    d = {'a': x if c1 else y, 'b': x if c2 else y, 'c': x if c3 else y}
"""


def f(a, b, c, x, y):
    d = {
        'a': x if a else y,
        'b': x if b else y,
        'c': x if c else y,
    }
    return d
