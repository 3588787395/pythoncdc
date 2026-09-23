def w(stocks, s1, s2):
    out = []
    for x in stocks:
        out.append(1 if x in s1 else (2 if x not in s2 else 3))
    return out
