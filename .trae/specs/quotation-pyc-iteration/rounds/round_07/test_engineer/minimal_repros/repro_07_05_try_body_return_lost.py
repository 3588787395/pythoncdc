"""Repro 07-05: D6 (P2) lost try-body return (te12 regression).

A try/except where the try body returns a constant and the except
returns a different value. The decompiler collapses the try body
`return 1` to `pass`, leaving only the except-side return.

Expected defect:
    def f():
        try:
            pass        # <- `return 1` lost
        except Exception:
            return 0
"""


def fetch_value():
    try:
        return 1
    except Exception:
        return 0
