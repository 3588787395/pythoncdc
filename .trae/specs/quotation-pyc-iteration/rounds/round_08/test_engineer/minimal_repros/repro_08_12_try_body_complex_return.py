"""Repro 08-12 (bonus): D6 with complex return expression.

D6 (try body return → pass) typically fires on `return <const>`. This
bonus repro checks whether a more complex try-body return expression
(`return compute(x) + 1`) is also lost.

Expected defect:
    def f(x):
        try:
            pass                    # <- `return compute(x) + 1` lost
        except Exception:
            return -1
"""


def f(x):
    try:
        return compute(x) + 1
    except Exception:
        return -1
