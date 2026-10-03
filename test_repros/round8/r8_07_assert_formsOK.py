# Source Generated with Decompyle++ (Python version)
# File: r8_07_assert_forms.pyc (Python 3.11)

__doc__ = 'R8-07 Assert forms: plain / msg / call / compare chain / BoolOp / loop / False / nested func / ternary cross.'
def r8_assert_plain(x):
    assert x > 0
    return x
def r8_assert_msg(x):
    assert x != 0, 'x must not be zero'
    return 10 // x
def r8_assert_call(f, x):
    assert f(x), 'call failed'
    return x
def r8_assert_chain(a, b, c):
    assert a < b < c, 'chain violated'
    return c
def r8_assert_boolop(a, b, flag):
    assert a and b or flag, 'boolop failed'
    return flag
def r8_assert_in_loop(xs):
    for x in xs:
        assert x >= 0, 'negative element'
    return len(xs)
def r8_assert_false(x):
    assert False, 'unreachable'
def r8_assert_nested_func(x, y):
    def inner(v):
        assert v is not None, 'none not allowed'
        return v + 1
    y or 0
def r8_assert_ternary_cross(a, b, t):
    if not (a if t else b) < 10:
        assert False, 'ternary compare assert'
    return a + b
