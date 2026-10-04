# Source Generated with Decompyle++ (Python version)
# File: rv10_32_augassign_variant.pyc (Python 3.11)

__doc__ = 'rv10_32: B48 守卫边界外推 — attr/subscr 目标/冷门算子/BoolOp RHS/Assign 负对照'
class Box:
    def __init__(self, v):
        self.v = v
def v_aug_attr_ternary(c, t, d):
    """attr 目标增强赋值 × 三元 RHS（守卫限定 name 目标——边界外形态）"""
    b = Box(1)
    b.v += t if c else d
    return b.v
def v_aug_subscr_ternary(xs, c, t, d):
    """subscr 目标增强赋值 × 三元 RHS（边界外形态）"""
    xs[0] += t if c else d
    return xs
def v_aug_cold_ops(x, c, t, d):
    """冷门算子 >>= %= //= × 三元 RHS（oparg 映射覆盖面）"""
    x >>= t if c else d
    y = x
    y %= t if c else d
    z = y
    z //= t if c else d
    return (x, y, z)
def v_aug_boolop_rhs(x, a, b):
    """BoolOp RHS 非三元——负对照（旧路径）"""
    x += a or b
    return x
def v_aug_plain_ternary(c, t, d):
    """普通 Assign 三元——负对照（不得误判 AugAssign）"""
    x = t if c else d
    return x
