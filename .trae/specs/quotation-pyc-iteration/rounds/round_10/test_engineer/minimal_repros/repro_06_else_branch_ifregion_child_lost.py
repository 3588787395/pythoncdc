"""R10 repro 06: IfRegion child not recognized in else branch.

Pattern: outer if's else branch contains a nested IfRegion. The
_if_generate_else_branch only collected TryExceptRegion/WithRegion/LoopRegion
children, not IfRegion, so the nested if was treated as a sequential block and
its condition was lost. Affects get_growth_ability (block 304).
"""
SOURCE = """
def f(x):
    if x == 0:
        return 0
    else:
        if x > 10:
            return 1
        elif x > 5:
            return 2
        else:
            return 3
"""

EXPECTED = SOURCE
