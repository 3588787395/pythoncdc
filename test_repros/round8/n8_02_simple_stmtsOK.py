# Source Generated with Decompyle++ (Python version)
# File: n8_02_simple_stmts.pyc (Python 3.11)

__doc__ = 'R8 negative control 2: simplest pass / assert / raise / del statements (must MATCH).'
def n8_pass_simple():
    return None
def n8_assert_simple(x):
    assert x > 0
    return x
def n8_raise_simple(x):
    if x < 0:
        raise ValueError
    return x
def n8_del_simple():
    a = 1
    del a
    return 0
