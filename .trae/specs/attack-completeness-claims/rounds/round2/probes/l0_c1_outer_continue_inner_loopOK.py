# Source Generated with Decompyle++ (Python version)
# File: l0_c1_outer_continue_inner_loop.pyc (Python 3.11)

__doc__ = 'AT-01: 内外双循环各自 continue —— 全局 CONTINUE 角色表的「哪一层循环」限定丢失'
def c1(xs):
    for a in xs:
        for b in xs:
            if b:
                continue
        if a:
            continue
