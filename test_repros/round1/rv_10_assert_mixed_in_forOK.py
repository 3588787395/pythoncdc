# Source Generated with Decompyle++ (Python version)
# File: rv_10_assert_mixed_in_for.pyc (Python 3.11)

def f(items, a, b, c):
    seen = 0
    for it in items:
        if not (a and b or c):
            assert False, 'rv10'
        seen += it
    return seen
