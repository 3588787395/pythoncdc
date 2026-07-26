"""Repro 06-08: Lost parens in BoolOp precedence.

Defect: `not (a == '0' and b == 1 or b == 2)` loses the inner grouping
parens, becoming `not (a == '0' and b == 1 or b == 2)` which actually
happens to be OK due to `and` binding tighter — but when the source had
explicit parens like `not (cond and (x or y))`, the inner parens are
dropped.

Variant: `if not (is_utc == '0' and typet in (1,2,3,4,5)):` —
the explicit grouping of `and` over `or` chains.
"""


def check(is_utc, typet):
    if not (is_utc == '0' and typet == 1 or typet == 2 or typet == 3):
        return True
    return False
