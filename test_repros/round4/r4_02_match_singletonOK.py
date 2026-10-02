# Source Generated with Decompyle++ (Python version)
# File: r4_02_match_singleton.pyc (Python 3.11)

def match_singleton_none(x):
    """Attack 1: None singleton case."""
    match x:
        case None:
            return 'is-none'
        case _:
            return 'not-none'
def match_singleton_bool(x):
    """Attack 2: True/False singleton cases (IS_OP based)."""
    match x:
        case True:
            return 'yes'
        case False:
            return 'no'
        case _:
            return 'maybe'
def match_singleton_mixed(x):
    """Attack 3: singleton mixed with value cases."""
    match x:
        case None:
            return 0
        case True:
            return 1
        case 0:
            return 2
        case 'z':
            return 3
        case _:
            return -1
def match_singleton_flag(state):
    """Attack 4: singleton guard-like dispatch table."""
    match state:
        case True:
            return 'enabled'
        case False:
            return 'disabled'
        case None:
            return 'unknown'
        case _:
            return 'default'
