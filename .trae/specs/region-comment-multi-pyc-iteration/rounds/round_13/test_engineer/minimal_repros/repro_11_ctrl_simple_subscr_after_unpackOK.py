# Source Generated with Decompyle++ (Python version)
# File: repro_11_ctrl_simple_subscr_after_unpack.pyc (Python 3.11)

__doc__ = """R13 repro_11 (CONTROL): simple subscript assign `x = df['col']` after
UNPACK_SEQUENCE. Confirms simple subscript (no COMPARE_OP) was never broken."""
def get_data():
    return ([1], None)
def f(flag, df):
    if flag:
        a, _ = get_data()
        x = df['col']
        if x:
            return a
