"""R13 repro_03: post-loop if/else not included in IfRegion else-branch.

Region type: LoopRegion + IfRegion (post-loop)
Violated principle: 3 (nesting as abstract node) — post-loop code should
be inside the enclosing IfRegion's else-branch, not a sibling
Corresponding function: get_date_and_count (block 1314)

Defect: After fixing the backward walk, the post-loop if/else (block 1314)
becomes a sibling IfRegion instead of being inside the if/elif/else chain's
else-branch. The AST generator merges the sibling conditions.
"""
def func(x, n):
    if x == 1:
        result = 1
    else:
        n -= 1
        while n > 0:
            if n > 10:
                n -= 5
            else:
                n -= 1
        if n in (0, 1, 2):
            result = 'low'
        else:
            result = 'high'
    return result
