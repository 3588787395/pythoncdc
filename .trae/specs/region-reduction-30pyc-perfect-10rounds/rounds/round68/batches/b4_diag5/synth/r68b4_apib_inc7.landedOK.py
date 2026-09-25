# Source Generated with Decompyle++ (Python version)
# File: r68b4_apib_inc7.pyc (Python 3.11)

def r68b4_apib_inc7(flag, a, b, c, include, min_count, am_close):
    tmp = b
    for _i in range(2):
        tmp = tmp
    if flag > 0:
        if a < b <= c:
            tmp = am_close
        min_count -= 1
        if flag > 100:
            min_count += 1
    elif flag < -100:
        min_count = 0
    return (tmp, min_count)
