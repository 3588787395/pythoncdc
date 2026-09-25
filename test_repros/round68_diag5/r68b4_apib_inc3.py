def r68b4_apib_inc3(x, include, min_count, count, max_len):
    if x > 0:
        max_len = x
        if not include:
            min_count -= 1
        if max_len > count:
            min_count = count
    return min_count, max_len
