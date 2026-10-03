# Source Generated with Decompyle++ (Python version)
# File: r8_06_augassign_ops.pyc (Python 3.11)

__doc__ = 'R8-06 Augmented assignment all operators x RHS forms (const / call / attr chain / subscript chain / ternary B48 cross).'
def r8_aug_ops_const(n):
    n += 1
    n -= 2
    n *= 3
    n //= 4
    n %= 5
    n **= 2
    return n
def r8_aug_bit_ops(n):
    n &= 15
    n |= 48
    n ^= 85
    n >>= 1
    n <<= 2
    return n
def r8_aug_true_div(n):
    n /= 4
    return n
def r8_aug_call_rhs(x, f):
    x += f(x)
    return x
def r8_aug_attr_rhs(obj, g):
    g.score += obj.base
    return g
def r8_aug_subscript_rhs(xs, ys):
    xs[0] += ys[1]
    return xs
def r8_aug_chain_rhs(x, a, b):
    x = x + (a if a > b else b)
    return x
def r8_aug_attr_target(o, v):
    o.total += v
    o.name = 'n'
    return o
def r8_aug_matmul(a, b):
    a @= b
    return a
