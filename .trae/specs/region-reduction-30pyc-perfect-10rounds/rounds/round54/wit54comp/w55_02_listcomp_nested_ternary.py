def w(stocks, s1, s2):
    return [1 if x in s1 else (2 if x not in s2 else 3) for x in stocks]
