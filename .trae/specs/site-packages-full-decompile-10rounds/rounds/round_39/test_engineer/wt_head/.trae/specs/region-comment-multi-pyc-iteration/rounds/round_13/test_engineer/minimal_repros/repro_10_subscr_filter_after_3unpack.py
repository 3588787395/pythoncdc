"""R13 repro_10: chained-subscript filter after UNPACK_SEQUENCE with 3 targets.
`a, b, c = call(); length = len(df[df['col'] > val])`."""


def get_data():
    return 1, 2, 3


def f(flag, df, val):
    if flag:
        a, b, c = get_data()
        length = len(df[df['col'] > val])
        if length > 0:
            return a + b + c
    return None
