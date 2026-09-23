def w(x, s1, s2):
    return max(1 if x in s1 else (2 if x not in s2 else 3), 0)
