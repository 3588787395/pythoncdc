def w(stocks, s1, s2):
    return {k: (1 if k not in s1 else (2 if k in s2 else 3)) for k in stocks}
