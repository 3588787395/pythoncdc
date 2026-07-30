"""Repro 05 - build_future_fill_time: minimal else with nested-if + trailing for-loop.

Reduced from repro_01: the else block has a nested if/else (setting m) FOLLOWED by a
for-loop. The if-branch (typet!=5) must jump PAST both the nested-if and the for-loop
to the trailing `if out:`. Decompiler hoists the for-loop to top level.

Key: the defect only triggers when the else block has BOTH a nested if/elif/else AND
a trailing for-loop. A bare for-loop in else (no preceding if) is handled correctly.
"""
def f(typet, suffix):
    days = [1, 2, 3]
    out = []
    if not typet == 5:
        for d in days:
            out.append(d)
    else:
        if suffix == 'A':
            m = [1]
        else:
            m = [2]
        for d in days:
            for v in m:
                out.append(d + v)
    if out:
        out.sort()
    return out
