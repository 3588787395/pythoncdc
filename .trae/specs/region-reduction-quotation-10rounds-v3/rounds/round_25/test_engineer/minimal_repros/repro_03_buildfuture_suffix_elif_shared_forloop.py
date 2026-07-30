"""Repro 03 - build_future_fill_time: typet elif chain WITHOUT trailing else + for-loop in else.

Matches the real function: typet==1/4/13 branches (no else) each have an internal loop
and jump past the shared for-loop. When no typet matches, still jump past the for-loop.
The else (typet==5) holds a nested if/elif/else that sets `m` + a shared for-loop.
"""
def f(typet, suffix):
    days = [1, 2, 3]
    out = []
    m = []
    if not typet == 5:
        if typet == 1:
            for d in days:
                out.append(d)
        elif typet == 4:
            for d in days:
                for v in m:
                    out.append(d + v)
        elif typet == 13:
            for d in days:
                for v in m:
                    out.append(d + v)
    else:
        if suffix == 'A':
            m = [1]
        elif suffix in ('B', 'C'):
            m = [2]
        else:
            m = [3]
        for d in days:
            for v in m:
                out.append(d + v)
    if out:
        out.sort()
    return out
