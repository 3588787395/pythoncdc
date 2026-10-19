def s_b73b(value, flag):
    try:
        return int(value)
    except ValueError as e:
        from math import floor as fl
        return fl(0) - len(str(e))
    finally:
        from math import ceil as ce
        if flag:
            ce(0)
