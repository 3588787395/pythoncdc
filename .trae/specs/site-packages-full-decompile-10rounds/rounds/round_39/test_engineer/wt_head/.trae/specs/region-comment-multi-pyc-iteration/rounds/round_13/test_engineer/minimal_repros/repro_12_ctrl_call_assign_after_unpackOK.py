# Source Generated with Decompyle++ (Python version)
# File: repro_12_ctrl_call_assign_after_unpack.pyc (Python 3.11)

__doc__ = """R13 repro_12 (CONTROL): simple call assign `x = len(df)` after UNPACK_SEQUENCE.
Confirms call assign without chained subscript was never broken."""
def get_data():
    return ([1], None)
def f(flag, df):
    if flag:
        a, _ = get_data()
        x = len(df)
        if x > 0:
            return a
