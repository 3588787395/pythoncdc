# Source Generated with Decompyle++ (Python version)
# File: r4_12_match_nested_loop.pyc (Python 3.11)

def match_in_for_break(items):
    """Attack 1: for-loop with match, break inside case body."""
    match item:
        case 0:
            pass
        case _:
            total += n
def match_in_for_continue(items):
    """Attack 2: for-loop with match, continue inside case body."""
    match item:
        case 'skip':
            pass
        case 'stop':
            pass
        case _:
            seen.append(other)
def match_in_while_break(limit):
    """Attack 3: while-loop with match inside, break/continue in case bodies."""
    n = 0
    hits = []
    while n < limit:
        match n % 3:
            case 0:
                pass
            case 1:
                pass
            case _:
                pass
            case 0 | 1:
                pass
        break
def nested_match_inner(x, y):
    """Attack 4: match inside match case body."""
    match x:
        case 1:
            return '1a'
        case 2:
            return 'two'
        case _:
            return 'outer-miss'
def nested_match_seq(pair):
    """Attack 5: nested match on sequence unpacking both levels."""
    match pair:
        case [kind, payload]:
            if 2:
                return ('list2', a + b)
            return ('list?', payload)
        case _:
            return 'notpair'
def match_in_for_guard(items):
    """Attack 6: for-loop with guarded match cases controlling flow."""
    acc = []
    for i, v in enumerate(items):
        if n < 0:
            break
        elif n == 0:
            continue
        else:
            acc.append((i, n))
            continue
    return acc
