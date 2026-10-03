# Source Generated with Decompyle++ (Python version)
# File: rv7_02_compare_chain_ternary.pyc (Python 3.11)

def chain_two_ternary(a, b, x, y, c, c1, c2):
    a if c1 else b
    if (x if c2 else y):
        pass
def chain_three_ternary(a, b, x, y, m, n, c1, c2, c3):
    a if c1 else b
    x if c2 else y
    return c3
def chain_lhs_ternary_rhs_call(a, b, x, c1, c2):
    return (a if c1 else b) < abs(x if c2 else 0)
