"""Repro 02 - build_future_fill_time: multiple typet elif branches (each with own loop) + shared for-loop in else.

Mirrors the real function: typet==1/2/3 branches each have an internal for-loop and
jump past the shared for-loop; the else (typet==5) sub-branches set `m` then share a for-loop.
"""
def f(typet, suffix):
    days = [1, 2, 3]
    out = []
    m = []
    if not typet == 5:
        if typet == 1:
            for d in days:
                out.append(d)
        elif typet == 2:
            for d in days:
                out.append(d * 2)
        elif typet == 3:
            for d in days:
                out.append(d * 3)
    else:
        if suffix == 'X':
            m = [10]
        elif suffix == 'Y':
            m = [20]
        else:
            m = [30]
        for d in days:
            for v in m:
                out.append(d + v)
    if out:
        out.sort()
    return out
