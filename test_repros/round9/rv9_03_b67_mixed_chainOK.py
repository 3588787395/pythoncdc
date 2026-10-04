# Source Generated with Decompyle++ (Python version)
# File: rv9_03_b67_mixed_chain.pyc (Python 3.11)

__doc__ = """rv9_03: B67 boundary attacks (round9 re-review, 9.3).

Units:
  or_and_chain  - mixed BoolOp (a or b and c) x continue
  and3_chain    - 3-member pure And chain x continue
  notnot_guard  - double negation guard x continue
"""
def or_and_chain(xs, a, b, c):
    for x in xs:
        if a(x) or b(x) and c(x):
            continue
        keep(x)
        continue
    return 11
def and3_chain(xs, a, b, c):
    for x in xs:
        if a(x) and b(x) and c(x):
            continue
        keep(x)
        continue
    return 12
def notnot_guard(xs, a):
    for x in xs:
        if a(x):
            continue
        keep(x)
        continue
    return 13
