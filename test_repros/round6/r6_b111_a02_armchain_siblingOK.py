# Source Generated with Decompyle++ (Python version)
# File: r6_b111_a02_armchain_sibling.pyc (Python 3.11)

__doc__ = 'r6_b111_a02: same arm exit, with a trailing sibling statement.'
def r6_b111_a02(start, end, limit, mode):
    if len(start) != 8 and len(start) != 12 or len(end) != 8 and len(end) != 12:
        return None
    else:
        total = 0
        if mode == 6:
            idx = 0
            while idx < limit:
                total = total + idx
                idx = idx + 1
        elif mode == 1:
            total = limit
        total = total + limit
        return total
