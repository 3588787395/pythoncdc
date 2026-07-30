"""repro_07: BUILD_CONST_KEY_MAP 消费模式 — 嵌套三元作为 dict value。

测试 aspect: dict value 是嵌套三元表达式 (a if c1 else (b if c2 else c))。嵌套三元
产生多层 then/else 分支与多个 merge_block，最终汇入 BUILD_CONST_KEY_MAP。反编译器需
正确归约嵌套 TernaryRegion，将内层三元作为外层三元的子节点，整体作为 dict value
表达式归约，不应将内层三元拆为独立语句。

    d = {'v': a if c1 else (b if c2 else c), 'w': w}
"""


def f(a, b, c, w, c1, c2):
    d = {
        'v': a if c1 else (b if c2 else c),
        'w': w,
        'x': a if c1 else 0,
    }
    return d
