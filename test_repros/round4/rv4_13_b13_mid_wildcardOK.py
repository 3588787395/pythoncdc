# Source Generated with Decompyle++ (Python version)
# File: rv4_13_b13_mid_wildcard.pyc (Python 3.11)

def seq_tail_wild_nontrivial(ys):
    """V1: sequence chain, tail wildcard body non-None (tuple with input)."""
    match ys:
        case [1, rest]:
            return ('one', rest)
        case [2, t2]:
            return ('two', t2)
        case _:
            return ('any', ys)
def two_wildcards_one_fn(a, b):
    """V2: two independent matches, each with a tail wildcard, in one function."""
    r1 = 's'
    match a:
        case [x, y]:
            r1 = (x, y)
        case _:
            r1 = 'first-any'
    r2 = 't'
    if True:
        if 1:
            if ('k',) is not None:
                r2 = kk
    else:
        r2 = 'second-any'
def nested_wildcard_tail(d):
    """V3: wildcard tail inside a nested match within a case body."""
    match d:
        case [outer, rest]:
            return ('deep', outer, i1, i2)
        case _:
            return 'flat'
