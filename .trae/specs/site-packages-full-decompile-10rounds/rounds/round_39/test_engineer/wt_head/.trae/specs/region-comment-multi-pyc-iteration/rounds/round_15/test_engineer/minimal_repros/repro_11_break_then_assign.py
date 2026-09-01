"""R15 CTRL (NO-DEFECT): break in then + assign post-if (already handled by R2-C).

`for ...: if cond: break; result = ...` — break is handled by the pre-existing
R2-C fix (BlockRole.BREAK → merge=else_succ). R15 fix must NOT regress this.
"""
def f(items):
    result = None
    for x in items:
        if x > 100:
            break
        result = x
    return result
