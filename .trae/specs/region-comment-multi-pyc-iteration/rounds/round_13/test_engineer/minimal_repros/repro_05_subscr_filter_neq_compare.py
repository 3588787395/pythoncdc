"""R13 repro_05: chained-subscript filter with different compare op (`!=`).
`length = len(df[df['col'] != val])` after UNPACK_SEQUENCE."""


def get_data():
    return [1], None


def f(flag, df, val):
    if flag:
        a, _ = get_data()
        length = len(df[df['col'] != val])
        if length > 0:
            return a
    return None
