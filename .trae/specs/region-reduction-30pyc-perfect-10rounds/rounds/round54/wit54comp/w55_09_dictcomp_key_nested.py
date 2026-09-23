def w(stocks, s1, s2):
    return {(x if x in s1 else (0 if x not in s2 else 1)): x for x in stocks}
