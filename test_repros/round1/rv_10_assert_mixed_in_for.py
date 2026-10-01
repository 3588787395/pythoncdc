# rv_10 修复二 assert and-run 前链吸收 嵌套变体：
# `assert a and b or c` 位于 for 体内（for > assert），且带消息参数


def f(items, a, b, c):
    seen = 0
    for it in items:
        assert a and b or c, "rv10"
        seen += it
    return seen
