"""Repro 08-08: D6 variant — try body return + except body return.

D6 (try body return → pass) appears most reliably when both try body
and except body return values. CPython 3.11 emits the try body's
RETURN_VALUE followed by RERAISE+COPY+POP_EXCEPT cleanup; the
decompiler may suppress both as cleanup and emit `pass` for the
try body.

Expected defect:
    def f():
        try:
            pass        # <- `return 1` lost
        except ValueError:
            return 0
"""


def f():
    try:
        return 1
    except ValueError:
        return 0
