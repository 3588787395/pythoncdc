"""repro_06: BUILD_CONST_KEY_MAP 消费模式 — 多个三元共享同一条件变量。

测试 aspect: dict 多个 value 是三元表达式且共享同一个条件变量 cond。CPython 会为每个
三元生成独立的 POP_JUMP + then/else 块，但这些三元的 merge_block 都流入同一个
BUILD_CONST_KEY_MAP。反编译器需识别这些三元共享消费点，整体归约而不遗漏中间三元。
若仅归约首个三元，后续三元的 value 表达式会丢失导致 dict 键数不匹配。

    d = {'a': x if cond else 0, 'b': y if cond else 0, 'c': z if cond else 0}
"""


def f(cond, x, y, z):
    d = {
        'a': x if cond else 0,
        'b': y if cond else 0,
        'c': z if cond else 0,
        'd': 1,
    }
    return d
