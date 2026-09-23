def w(stocks, s1, s2, s3):
    return [1 if x in s1 else (2 if x in s2 else (3 if x not in s3 else 4)) for x in stocks]
