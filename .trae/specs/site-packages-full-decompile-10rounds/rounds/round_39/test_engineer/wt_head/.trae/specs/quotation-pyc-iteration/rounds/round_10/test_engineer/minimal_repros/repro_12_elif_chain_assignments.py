"""R10 repro 12: elif chain with assignment in each elif condition.

Pattern: each elif condition block contains an assignment before the test.
All assignments must be preserved as pre-stmts before each elif.
"""
SOURCE = """
def f(a, b, c):
    if a == 0:
        return 0
    x = a + 1
    if x > 10:
        return 1
    y = b + 2
    if y > 10:
        return 2
    z = c + 3
    if z > 10:
        return 3
    return -1
"""

EXPECTED = SOURCE
