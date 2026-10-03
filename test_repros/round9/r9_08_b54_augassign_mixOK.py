# Source Generated with Decompyle++ (Python version)
# File: r9_08_b54_augassign_mix.pyc (Python 3.11)

__doc__ = """Round 9 守卫面新构造 8：B54 链式赋值 × augassign 混合 × B2 continue 守卫。

攻击清单第 4 项：B54 链式赋值 × augassign 混合。链式赋值（B54 判据面）
与增量赋值在同一循环体内交叠、continue 守卫横跨其间。
"""
def chain_aug_loop(xs, a):
    acc = 0
    for i in xs:
        n = (m := i)
        if a(i):
            continue
        acc += m + n
        continue
    return acc
def chain_then_aug(a, b):
    p = q = a + b
    p *= 2
    q -= 1
    return p + q
def aug_chain_while(a, b):
    while a:
        v = (u := a)
        if b(u):
            break
        v += 3
        a = v - 1
    return a
