"""R13 repro_10: while loop after if/elif chain (sibling, not nested).

Region type: IfRegion + LoopRegion (sequential)
Violated principle: 3 (nesting as abstract node) — the while loop and
post-loop code should be inside the if/elif/else chain's else-branch
Corresponding function: get_date_and_count (general pattern)

Defect: The if/elif/else chain's else-branch contains a while loop
followed by an if/else. The region hierarchy should nest the while loop
and post-loop if/else inside the IfRegion's else-branch, but the current
implementation treats them as siblings.
"""
def func(a, b, c):
    if a == 0:
        result = 0
    elif b == 1:
        result = 1
    else:
        c -= 1
        while c > 0:
            if c > 5:
                c -= 3
            else:
                c -= 1
        if c == 0:
            result = 'zero'
        else:
            result = 'nonzero'
    return result
