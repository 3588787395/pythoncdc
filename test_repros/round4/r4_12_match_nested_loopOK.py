# Source Generated with Decompyle++ (Python version)
# File: r4_12_match_nested_loop.pyc (Python 3.11)

def match_in_for_break(items):
    """Attack 1: for-loop with match, break inside case body."""
    total = 0
    for item in items:
        match item:
            case 0:
                break
            case n:
                total += n
    return total
def match_in_for_continue(items):
    """Attack 2: for-loop with match, continue inside case body."""
    seen = []
    for item in items:
        match item:
            case 'skip':
                pass
            case 'stop':
                break
            case other:
                seen.append(other)
    return seen
def match_in_while_break(limit):
    """Attack 3: while-loop with match inside, break/continue in case bodies."""
    n = 0
    hits = []
    while n < limit:
        n += 1
        match n % 3:
            case 0:
                continue
            case 1:
                hits.append(n)
            case _:
                if n > limit - 2:
                    break
    return hits
def nested_match_inner(x, y):
    """Attack 4: match inside match case body."""
    match x:
        case 1:
            match y:
                case 'a':
                    return '1a'
                case 'b':
                    return '1b'
                case _:
                    return '1?'
        case 2:
            return 'two'
        case _:
            return 'outer-miss'
def nested_match_seq(pair):
    """Attack 5: nested match on sequence unpacking both levels."""
    match pair:
        case [kind, payload]:
            match kind:
                case 'list':
                    match payload:
                        case [a, b]:
                            return ('list2', a + b)
                        case _:
                            return ('list?', payload)
                case 'num':
                    return ('num', payload * 2)
                case _:
                    return ('unknown-kind', kind)
        case _:
            return 'notpair'
def match_in_for_guard(items):
    """Attack 6: for-loop with guarded match cases controlling flow."""
    acc = []
    for i, v in enumerate(items):
        match v:
            case n if n < 0:
                break
            case n:
                pass
            case n:
                acc.append((i, n))
    return acc
