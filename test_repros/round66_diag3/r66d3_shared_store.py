def p1(data_count, symbols):
    data_count = int(data_count) if 0 < int(data_count) <= 200 else 200
    if isinstance(symbols, str):
        symbols = [symbols]
    return data_count, symbols


def p2(data_count, symbols):
    if 0 < int(data_count) <= 200:
        data_count = int(data_count)
    else:
        data_count = 200
    if isinstance(symbols, str):
        symbols = [symbols]
    return data_count, symbols
