"""R13 repro_11 (CONTROL): simple subscript assign `x = df['col']` after
UNPACK_SEQUENCE. Confirms simple subscript (no COMPARE_OP) was never broken."""


def get_data():
    return [1], None


def f(flag, df):
    if flag:
        a, _ = get_data()
        x = df['col']
        if x:
            return a
    return None
