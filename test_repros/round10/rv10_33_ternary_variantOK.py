# Source Generated with Decompyle++ (Python version)
# File: rv10_33_ternary_variant.pyc (Python 3.11)

__doc__ = 'rv10_33: B46 守卫边界外推 — false 臂嵌套/三层嵌套/return 位/语句逃逸负对照/BoolOp 条件'
def v_nest_false_arm(c1, c2, a, b, d):
    """false 臂嵌套三元（false_existing=TernaryRegion 既有对称通道）"""
    return a if c1 else b if c2 else d
def v_nest_three_level(c1, c2, c3):
    """三层嵌套三元"""
    return 1 if c1 else 2 if c2 else 3 if c3 else 4
def v_nest_return_pos(xs, c1, c2):
    """return 位嵌套三元 + 前导循环"""
    acc = 0
    for x in xs:
        acc += x
    return acc if c1 else acc * 2 if c2 else -acc
def v_nest_escape_neg(c1, c2):
    """负对照：true 臂为嵌套 if 语句（跳转逃逸内层区域）——守卫必须拒绝放行"""
    if c1:
        if c2:
            x = 1
        else:
            x = 2
    else:
        y = 9
    return (x, y)
def v_nest_and_combo(v, c1, c2):
    """外层条件含 BoolOp + true 臂嵌套三元"""
    return v if c1 and c2 else v * 2 if v > 0 else -v
