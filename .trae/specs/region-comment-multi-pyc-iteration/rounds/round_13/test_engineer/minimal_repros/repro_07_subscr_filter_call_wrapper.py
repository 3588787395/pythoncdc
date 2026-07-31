"""R13 repro_07: chained-subscript filter with call wrapper other than len.
`x = list(df[df['col'] > val])` after UNPACK_SEQUENCE."""


def get_data():
    return [1], None


def f(flag, df, val):
    if flag:
        a, _ = get_data()
        result = list(df[df['col'] > val])
        if result:
            return a
    return None
