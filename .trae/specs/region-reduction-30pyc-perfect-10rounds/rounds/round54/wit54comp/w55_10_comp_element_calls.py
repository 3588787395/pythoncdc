def w(stocks, s1, s2):
    return [str(x) if x in s1 else (repr(x) if x not in s2 else len(str(x))) for x in stocks]
