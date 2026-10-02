# Source Generated with Decompyle++ (Python version)
# File: rv4_15_b15_leading_dual_exit.pyc (Python 3.11)

def leading_multi(x):
    """V1: three leading statements before match, shared fall-through tail."""
    acc = []
    log = 'start'
    total = 0
    match x:
        case 1:
            acc.append('one')
        case 2:
            acc.append('two')
    acc.append(log)
    total = len(acc)
    return (acc, total)
def dual_exit(x):
    """V2: one case returns early, other falls through (dual exit)."""
    flag = None
    match x:
        case 1:
            flag = 'one'
        case 2:
            return 'two-direct'
    flag = flag + '!'
    return flag
def shared_tail_after_match(v):
    """V3: leading init + match + post statements using pre-match names."""
    base = v * 2
    label = 'n'
    match v:
        case 0:
            label = 'zero'
        case 1:
            label = 'one'
        case 3:
            return ('three', base)
    return (label, base)
