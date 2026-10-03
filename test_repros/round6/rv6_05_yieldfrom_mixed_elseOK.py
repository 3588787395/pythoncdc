# Source Generated with Decompyle++ (Python version)
# File: rv6_05_yieldfrom_mixed_else.pyc (Python 3.11)

__doc__ = """rv6_05: yield from 混合 else（B35 变体）——for-else 内 yield from + 夹层 yield + 三段交替。

对照 r6_15.g_mixed（yield from xs; yield 0; yield from ys）：
换宿主结构（for-else 内 yield from、三段交替双夹层），检验混合 else 块
拆分判据在多夹层/for-else 宿主下是否仍按语句屏障正确切分。
"""
def gen_for_else_mixed(xs, ys):
    for x in xs:
        yield from x
    yield from ys
def gen_three_alternate(xs, ys, zs):
    yield from xs
    yield 1
    yield from ys
    yield 2
    yield from zs
def gen_call_form_mid(xs, n):
    yield from range(n)
    yield -1
    yield from xs
