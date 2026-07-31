# Source Generated with Decompyle++ (Python version)
# File: repro_04_subscr_filter_after_plain_store.pyc (Python 3.11)

__doc__ = """R13 repro_04: chained-subscript filter in if-body after a plain STORE_FAST
(not UNPACK_SEQUENCE). Confirms the bug triggers with any preceding STORE."""
def f(df, val, flag):
    if flag:
        tmp = df['col']
        length = len(df[df['col'] > val])
        if length > 0:
            return tmp
