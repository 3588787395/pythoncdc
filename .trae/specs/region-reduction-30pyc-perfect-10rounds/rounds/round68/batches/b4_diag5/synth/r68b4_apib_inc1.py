def r68b4_apib_inc1(a, b, c, include, min_count, pm_open, am_close):
    tmp = b
    if a < b <= c:
        tmp = am_close
        if not include:
            min_count -= 1
    return tmp, min_count
