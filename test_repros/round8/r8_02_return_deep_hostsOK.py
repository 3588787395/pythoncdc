# Source Generated with Decompyle++ (Python version)
# File: r8_02_return_deep_hosts.pyc (Python 3.11)

__doc__ = 'R8-02 Return pushed into deep hosts: while-break / try-else / with / match / async / lambda / nest >=3.'
def r8_ret_while_break(n):
    while True:
        n -= 1
        if n <= 3:
            break
    return n
def r8_ret_try_else(xs, i):
    try:
        v = xs[i]
    except IndexError:
        return 'idx'
    else:
        return v
    finally:
        pass
def r8_ret_with(path):
    with open(path) as fh:
        return fh.read(3)
def r8_ret_match(x):
    match x:
        case {'k': v}:
            return v
        case [a, b]:
            return a + b
        case str() as s:
            return s.upper()
async def r8_ret_await(io):
    return await io.fetch()
def r8_ret_lambda_ternary(flag):
    f = lambda v: v if flag else 0
    return f(7)
def r8_ret_deep_nest(a, b, c):
    if a:
        for i in range(3):
            if b:
                while c:
                    c -= 1
                return i
        return -2
    else:
        return -1
def r8_ret_gen_deep(n):
    for k in range(n):
        if k % 2:
            yield k
    return n
