# Source Generated with Decompyle++ (Python version)
# File: r4_09_match_guard.pyc (Python 3.11)

def match_guard_capture(x):
    """Attack 1: guard on a capture pattern."""
    if v > 0:
        return ('pos', v)
    elif v < 0:
        return ('neg', v)
    else:
        return 'zero'
def match_guard_value(x):
    """Attack 2: guard on a value case."""
    match x:
        case 1 if x > 0:
            return 'one-pos'
        case 1:
            return 'one-neg'
        case _:
            return 'other'
def match_guard_seq(seq):
    """Attack 3: guard on sequence pattern."""
    match seq:
        case [a, b] if a < b:
            return ('asc', a, b)
        case [a, b] if a > b:
            return ('desc', a, b)
        case [a, b]:
            return ('eq', a)
        case _:
            return 'notpair'
def match_guard_mixed_multi(x):
    """Attack 4: guards interleaved with plain cases (multi-case + guard mixed)."""
    match x:
        case 0:
            return 'zero'
        case v if v % 2 == 0:
            return ('even', v)
        case 3 | 5 | 7:
            return 'prime-odd'
        case v if v % 2 == 1:
            return ('odd', v)
        case _:
            return 'huge'
def match_guard_bool(x):
    """Attack 5: guard with boolean-combined condition."""
    if v > 0 and v < 10:
        return 'digit'
    if v >= 10 or v == -5:
        return 'edge'
    match v:
        case -5:
            pass
        case _:
            return 'other'
def match_guard_class(p):
    """Attack 6: guard on class pattern."""
    match p:
        case [a, b] if a == b:
            return 'same'
        case [a, b]:
            return 'sum10'
        case _:
            return 'plain'
