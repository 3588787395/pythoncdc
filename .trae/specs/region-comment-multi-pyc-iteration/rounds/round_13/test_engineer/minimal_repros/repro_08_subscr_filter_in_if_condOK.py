# Source Generated with Decompyle++ (Python version)
# File: repro_08_subscr_filter_in_if_cond.pyc (Python 3.11)

__doc__ = """R13 repro_08: chained-subscript filter directly as if-condition argument
(nested in call). `if len(df[df['col'] > val]) > 0:` after UNPACK_SEQUENCE."""
def get_data():
    return ([1], None)
def f(flag, df, val):
    if flag:
        a, _ = get_data()
        if len(df[df['col'] > val]) > 0:
            return a
