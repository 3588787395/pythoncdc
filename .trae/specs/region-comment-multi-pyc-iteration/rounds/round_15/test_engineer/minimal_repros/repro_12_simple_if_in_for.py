"""R15 CTRL (NO-DEFECT): simple if in for-loop, no continue (pure control).

`for ...: if cond: total += ...` — no continue/break. Verifies R15 fix does not
affect normal if-in-loop (no JUMP_BACKWARD in then_succ → fix not triggered).
"""
def f(items):
    total = 0
    for x in items:
        if x > 0:
            total += x
    return total
