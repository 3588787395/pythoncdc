"""Round 9 B3 守卫族回归攻击 4：R71-thenover / W23 merge 共享尾归属（loop 帧内）。

攻击面：[R71-thenover]（region_ast_generator.py:24739/24744，merge_block ∈
候选区域 else_blocks 的影子认领）与 [W23]（:21161 嵌套内层 IfRegion 与
外层共享尾跨层唯一归属）。守卫边界外邻接形态：elif 链 + 尾语句在
循环帧内的归属竞争。
"""


def elif_shared_tail(a, b, xs):
    for i in xs:
        if a(i):
            arm1(i)
        elif b(i):
            arm2(i)
        shared(i)
    return 1


def if_elif_deep_shared(a, b, c, xs):
    for i in xs:
        if a(i):
            if b(i):
                arm(i)
            else:
                other(i)
        elif c(i):
            third(i)
        tail(i)
    return 2


def while_elif_shared(a, b):
    while a:
        if b():
            p = 1
        elif a > 5:
            p = 2
        else:
            p = 3
        out(p)
        a = a - 1
    return 3
