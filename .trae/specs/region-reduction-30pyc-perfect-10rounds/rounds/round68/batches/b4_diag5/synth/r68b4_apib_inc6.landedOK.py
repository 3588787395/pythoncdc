# Source Generated with Decompyle++ (Python version)
# File: r68b4_apib_inc6.pyc (Python 3.11)

def r68b4_apib_inc6(flag, a, b, c, include, min_count, am_close):
    tmp = b
    if flag > 0 and flag < 1000:
        if a < b <= c:
            tmp = am_close
            if not include:
                min_count -= 1
        else:
            return (tmp, min_count)
    elif flag < -100:
        min_count = 0
