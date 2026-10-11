# Source Generated with Decompyle++ (Python version)
# File: r8v8fc_b81_t2_wildguard.pyc (Python 3.11)

def t2_wildcard_guard(y):
    match x:
        case _ if y > 0:
            return 1
        case _:
            return 2
def t2_wildcard_guard_mid(y):
    match x:
        case 1:
            return 'one'
        case _ if y > 0:
            return 'pos'
        case _:
            return 'other'
