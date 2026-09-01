# Source Generated with Decompyle++ (Python version)
# File: repro_09_subscr_filter_attr_index.pyc (Python 3.11)

__doc__ = """R13 repro_09: chained-subscript filter with attribute access index
`df[df.col > val]` after UNPACK_SEQUENCE."""
def get_data():
    return ([1], None)
def f(flag, df, val):
    if flag:
        a, _ = get_data()
        length = len(df[df.col > val])
        if length > 0:
            return a
