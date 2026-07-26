"""Repro 09-02: D3 baseline — chained compare in except (isolated).

R8 repro_08_01 / repro_08_07 / repro_08_11 all showed that the chained
compare `if 400 <= e.code <= 499:` SURVIVES in isolation (NOT-REPRO).
This repro is the R9 baseline confirming that D3 still does NOT fire
without the preceding call. It serves as a control case for repro_09_01.

Expected: NOT-REPRO (chained compare preserved).
If this becomes DEFECT-REPRO, D3 has widened (regression).
"""


def handler(e):
    try:
        do_work()
    except HTTPError as e2:
        if 400 <= e2.code <= 499:
            handle_4xx(e2)
        else:
            handle_other(e2)
