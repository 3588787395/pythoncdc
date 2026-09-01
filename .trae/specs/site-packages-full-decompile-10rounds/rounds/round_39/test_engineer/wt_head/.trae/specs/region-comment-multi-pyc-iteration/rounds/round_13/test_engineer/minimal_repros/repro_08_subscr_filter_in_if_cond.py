"""R13 repro_08: chained-subscript filter directly as if-condition argument
(nested in call). `if len(df[df['col'] > val]) > 0:` after UNPACK_SEQUENCE."""


def get_data():
    return [1], None


def f(flag, df, val):
    if flag:
        a, _ = get_data()
        if len(df[df['col'] > val]) > 0:
            return a
    return None
