# Source Generated with Decompyle++ (Python version)
# File: r6_b111_a01_armchain_twin.pyc (Python 3.11)

__doc__ = 'r6_b111_a01: if-arm exit of a mixed `and/or/and` chain, no trailing sibling.'
def r6_b111_a01(start, end, limit, mode):
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
            idx = 0
            while idx < limit:
                total = total - idx
                idx = idx + 1
        return total
