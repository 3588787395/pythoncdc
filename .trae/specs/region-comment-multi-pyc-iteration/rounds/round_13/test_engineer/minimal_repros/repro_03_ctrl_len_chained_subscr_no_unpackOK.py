# Source Generated with Decompyle++ (Python version)
# File: repro_03_ctrl_len_chained_subscr_no_unpack.pyc (Python 3.11)

__doc__ = """R13 repro_03 (CONTROL): `length = len(df[df['col'] > val])` WITHOUT preceding
UNPACK_SEQUENCE. Confirms the bug requires the prior STORE to set pre_seen_store.
"""
def f(df, val):
    length = len(df[df['col'] > val])
    if length > 0:
        return 1
    else:
        return 0
