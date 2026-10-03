# Source Generated with Decompyle++ (Python version)
# File: r9_05_b4_orphan_release.pyc (Python 3.11)

__doc__ = """Round 9 B4 守卫族回归攻击 5：孤儿块释放守卫边界（含 R74 fix1 abs2 覆盖集边界）。

攻击面：generate() 顶部孤儿块释放（region_ast_generator.py:1636-1696）——
「顶级祖先 + 父发射集合交集」豁免的边界外形态：嵌套 if/elif 链的
merge 块落在父区域 blocks 之外时的释放与补发射。
"""
def elif_orphan_shape(a, b, xs):
    for x in xs:
        if a(x):
            pass
        elif b(x):
            y = 1
        z = 2
    return 3
def deep_if_else_cascade(a, b, c, d):
    if a:
        if b:
            if c:
                r = 1
            else:
                r = 2
        else:
            r = 3
    else:
        r = 4
    return r
def loop_orphan_elif(a, b, c):
    while a:
        if b:
            t = 1
        elif c:
            t = 2
        a = a - 1
    return t
