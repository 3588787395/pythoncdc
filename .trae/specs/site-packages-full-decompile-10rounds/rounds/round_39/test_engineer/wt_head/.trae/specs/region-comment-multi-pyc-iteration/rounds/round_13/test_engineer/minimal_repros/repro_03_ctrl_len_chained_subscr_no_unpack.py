"""R13 repro_03 (CONTROL): `length = len(df[df['col'] > val])` WITHOUT preceding
UNPACK_SEQUENCE. Confirms the bug requires the prior STORE to set pre_seen_store.
"""


def f(df, val):
    length = len(df[df['col'] > val])
    if length > 0:
        return 1
    return 0
