"""复现 07：后置嵌套双循环（外层 + 内层 FOR_ITER）。

模式：后置块为两层 for 循环，外层 FOR_ITER exit=hi，内层 FOR_ITER exit=外层 JUMP_BACKWARD。
JUMP_BACKWARD(外层) 位于 hi-1，回跳到外层 FOR_ITER。
"""
def f(n, outer, inner):
    acc = []
    if n > 0:
        for o in outer:
            acc.append(o)
    for o in outer:
        for i in inner:
            acc.append(o + i)
    return acc
