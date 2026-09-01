"""Repro 10 (control): no f-string, COMPARE_OP in if condition.

Verifies the original clearing heuristic still works for the normal
case (if condition after pre-statements, no f-string). Expected: the
if condition is correctly extracted.
"""
def f(a, b):
    x = a + b
    if x == 0:
        return x
    return -1
