# Source Generated with Decompyle++ (Python version)
# File: rv4_16_b16_loop_nest.pyc (Python 3.11)

def while_match_match(n, xs):
    """V1: while > match > match (three layers) with break/continue bodies."""
    out = []
    i = 0
    while i < n:
        match i % 3:
            case 0:
                if xs[i % len(xs)] == 'a':
                    out.append('A')
                else:
                    out.append('a?')
            case 1:
                out.append('B')
    return out
def for_match_while(n):
    """V2: for > match > while (match body contains a while loop)."""
    total = 0
    for k in range(n):
        if k % 2 == 0:
            j = 0
            while j < 2:
                total += k
                j += 1
    return total
def while_match_continue(m):
    """V3: while > match with continue targeting the outer loop."""
    seen = []
    k = 0
    while k < m:
        k += 1
        match k % 4:
            case 1:
                continue
            case 2:
                seen.append('two')
            case 3:
                seen.append('three')
    return seen
