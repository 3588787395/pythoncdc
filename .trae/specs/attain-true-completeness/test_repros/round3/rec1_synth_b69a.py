def s_b69a(a):
    if a:
        try:
            a += 1
        finally:
            a += 2
        return a
    else:
        return 0
