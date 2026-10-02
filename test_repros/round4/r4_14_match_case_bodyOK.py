# Source Generated with Decompyle++ (Python version)
# File: r4_14_match_case_body.pyc (Python 3.11)

def match_case_return(x):
    """Attack 1: return inside case bodies."""
    match x:
        case 'a':
            return 1
        case 'b':
            return 2
        case _:
            return 3
def match_case_shared_body(x):
    """Attack 2: fall-through — multiple case labels sharing one body before break."""
    match x:
        case 1:
            pass
        case 2:
            pass
        case _:
            if x == 1 or x == 2:
                result = 'low'
            else:
                result = 'high'
            return result
def match_case_ifelse_body(x):
    """Attack 3: case body containing if/else with boolop conditions."""
    if n > 0 and x % 2 == 0:
        return 'pos-even'
    if n > 0 or n == -100:
        return 'pos-or-special'
    match n:
        case -100:
            pass
        case _ if x != 0:
            pass
    return 'weird'
def match_case_early_return_loop(x):
    """Attack 4: case body returns from inside a loop (early return)."""
    lst = x
    for item in lst:
        if item > 5:
            return ('big', item)
        elif item < 0:
            return ('neg', item)
        else:
            continue
    return 'all-small'
def match_case_multi_stmt(x):
    """Attack 5: case bodies with multiple statements including nested if/else."""
    match 0:
        case 1 as acc:
            acc *= 10
        case 2:
            acc += 2
            if acc and x:
                acc *= 20
            else:
                acc = -1
        case _:
            acc = 100
def match_case_bool_guard(x, y):
    """Attack 6: guards with or-chains and boolean combinations."""
    if a == 1 or a == 2 or y == 3:
        return 'first'
    else:
        if a > 3 and y < 0 and a != 9:
            return 'second'
        if not (a or y):
            return 'third'
        else:
            return 'fourth'
