def boolop_in_if(a, b, c):
    if a > 0 and b > 0:
        return c
    elif a < 0 or b < 0:
        return -c
    else:
        return 0
