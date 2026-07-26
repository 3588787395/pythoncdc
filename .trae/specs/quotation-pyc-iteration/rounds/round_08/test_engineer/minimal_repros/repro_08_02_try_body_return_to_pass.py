"""Repro 08-02: D6 (P2) try body return lost → pass.

A try/except where the try body returns a constant and the except
returns a different value. CPython 3.11 emits a `RERAISE`+`COPY`+`POP_EXCEPT`
cleanup block after the try body's RETURN_VALUE, which the decompiler
suppresses, but in doing so it also drops the genuine `return 1` and
emits `pass` instead. Confirmed by te12tryexceptreturn_valueerror.

Expected defect:
    def f():
        try:
            pass        # <- `return 1` lost
        except ValueError:
            return 0
"""


def fetch_value():
    try:
        return 1
    except ValueError:
        return 0
