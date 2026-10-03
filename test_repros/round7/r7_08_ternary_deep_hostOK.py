# Source Generated with Decompyle++ (Python version)
# File: r7_08_ternary_deep_host.pyc (Python 3.11)

__doc__ = 'R7-08 三元深层宿主面（if/while/for-else/try/with/match/async）。'
def t_host_if_arms(x, flag):
    if x > 0:
        r = 'pos' if flag else 'pos2'
    else:
        r = 'neg' if flag else 'neg2'
    return r
def t_host_while_body(n, flag):
    acc = 0
    while n > 0:
        acc = acc + (n if flag else 1)
        n -= 1
    return acc
def t_host_for_else(xs, flag):
    total = 0
    for x in xs:
        total = total + (x if flag else 0)
    total = total + (100 if flag else 1)
    return total
def t_host_try_sections(xs, i, flag):
    try:
        r = r if flag else 0
        return r
    except IndexError:
        r = -1 if flag else -2
    finally:
        r = r if flag else 0
def t_host_with_body(path, flag):
    with open(path) as fh:
        data = fh.read(1 if flag else 2)
    return data
def t_host_match_case(x, flag):
    match x:
        case 1:
            if flag:
                return 'one'
            else:
                return '1'
        case 2:
            if flag:
                return 'two'
            else:
                return '2'
        case _:
            if flag:
                return 'other'
            else:
                return '?'
async def t_host_async_for_body(agen, flag):
    out = []
    async for v in agen:
        out.append(v if flag else 0)
    return out
