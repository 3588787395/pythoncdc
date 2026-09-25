def r68b4_apib_inc4(flag, a, b, c, include, min_count, am_close):
    tmp = b
    if flag > 0:
        if a < b <= c:
            tmp = am_close
            if not include:
                min_count -= 1
        if flag > 100:
            min_count += 1
    elif flag < -100:
        min_count = 0
    return tmp, min_count
