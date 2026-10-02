# rv4 (REVIEW2 variant): B13 - wildcard tail variants (3.11 forbids non-tail wildcard,
# so middle-position coverage = wildcard tail in nested/multiple matches in one function)


def seq_tail_wild_nontrivial(ys):
    """V1: sequence chain, tail wildcard body non-None (tuple with input)."""
    match ys:
        case [1, rest]:
            return ("one", rest)
        case (2, t2):
            return ("two", t2)
        case _:
            return ("any", ys)


def two_wildcards_one_fn(a, b):
    """V2: two independent matches, each with a tail wildcard, in one function."""
    r1 = "s"
    match a:
        case [x, y]:
            r1 = (x, y)
        case _:
            r1 = "first-any"
    r2 = "t"
    match b:
        case {"k": kk}:
            r2 = kk
        case _:
            r2 = "second-any"
    return (r1, r2)


def nested_wildcard_tail(d):
    """V3: wildcard tail inside a nested match within a case body."""
    match d:
        case [outer, rest]:
            match rest:
                case [i1, i2]:
                    return ("deep", outer, i1, i2)
                case _:
                    return ("deep-any", outer)
        case _:
            return "flat"
