"""R15 CTRL (fix-validation): continue in then + simple assign post-if.

`for ...: if cond: continue; result.append(...)` — the method-call statement is
the post-if statement. R15 fix ensures merge=else_succ (the append block), so
the append is generated as a post-if loop-body statement, not an else-branch.
"""
def f(items):
    result = []
    for x in items:
        if x < 0:
            continue
        result.append(x * 2)
    return result
