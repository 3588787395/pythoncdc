"""R10 repro 10: nested IfRegion in else branch with trailing statements.

Pattern: outer if's else branch contains a nested IfRegion followed by more
sequential statements. The trailing statements after the nested IfRegion were
lost because the else-branch interleaving didn't properly emit seq blocks
after child regions.
"""
SOURCE = """
def f(x):
    if x == 0:
        return 0
    else:
        if x > 10:
            y = 1
        else:
            y = 2
        z = y + 1
        return z
"""

EXPECTED = SOURCE
