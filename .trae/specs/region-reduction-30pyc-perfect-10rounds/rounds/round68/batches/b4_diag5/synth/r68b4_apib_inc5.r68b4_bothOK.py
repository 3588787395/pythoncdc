# Source Generated with Decompyle++ (Python version)
# File: r68b4_apib_inc5.pyc (Python 3.11)

def r68b4_apib_inc5(flag, a, b, include, min_count, am_close):
    tmp = b
    if flag > 0:
        if a > b:
            tmp = am_close
            if not include:
                min_count -= 1
        if flag > 100:
            min_count += 1
    elif flag < -100:
        min_count = 0
    return (tmp, min_count)
