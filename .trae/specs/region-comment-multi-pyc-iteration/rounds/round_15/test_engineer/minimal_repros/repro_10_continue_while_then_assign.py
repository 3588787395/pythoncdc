"""R15 CTRL (fix-validation): continue in while-loop then + assign post-if.

`while ...: if cond: continue; total += ...` — continue inside a while-loop.
R15 fix is loop-type agnostic (header_block applies to both FOR and WHILE
LoopRegion), so the assign is correctly placed as a post-if statement.
"""
def f(n):
    i = 0
    total = 0
    while i < n:
        i += 1
        if i % 2 == 0:
            continue
        total += i
    return total
