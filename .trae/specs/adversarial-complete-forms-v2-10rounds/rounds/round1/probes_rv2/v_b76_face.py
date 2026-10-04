"""rv2 变体面 B76（rv10_32 v_aug_boolop_rhs 邻域）：BoolOp×Compare 链 / 三链 or / 负对照"""


def v_cmp_chain(x, a, b):
    x += a and b > 0
    return x


def v_or3_chain(x, a, b, c):
    x -= a or b or c
    return x


def n_mul_and(x, a, b):
    x *= b and a
    return x
