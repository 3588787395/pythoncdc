# Source Generated with Decompyle++ (Python version)
# File: r6_b111_a03_armends_fn_control.pyc (Python 3.11)

__doc__ = 'r6_b111_a03 control: the arm really ends the function (no chain fold).'
def r6_b111_a03(start, limit):
    total = 0
    idx = 0
    while idx < limit:
        total = total + idx
        idx = idx + 1
    if len(start) != 8:
        return total
    else:
        return None
