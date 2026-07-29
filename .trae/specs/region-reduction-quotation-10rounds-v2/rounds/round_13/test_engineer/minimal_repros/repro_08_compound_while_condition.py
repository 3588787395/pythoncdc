"""R13 repro_08: compound while condition (true condition-chain predecessor).

Region type: LoopRegion (compound condition)
Violated principle: N/A (control case — true condition-chain predecessor)
Corresponding function: N/A (control for backward walk fix)

Defect: `while (a or b) and c:` has a chain of FORWARD_CONDITIONAL_JUMP
blocks where each operand's fall-through flows to the next operand (the
condition_block). The backward walk correctly absorbs these as
condition-chain predecessors because fall-through == _cb. This repro
verifies the fix doesn't break this case.
"""
def func(a, b, c):
    while (a or b) and c:
        a = a - 1
        b = b - 1
        c = c - 1
    return (a, b, c)
