# n4_01 negative control: no match — equivalent if/elif chain + simple loops


def ifelif_value_single(x):
    """Control 1: equivalent of single value case."""
    if x == 1:
        return "one"
    else:
        return "other"


def ifelif_mixed_types(x):
    """Control 2: equivalent of mixed-type multi-case."""
    if x == 1:
        return "int-one"
    elif x == "hello":
        return "str-hello"
    elif x == 3.5:
        return "float"
    elif x is None:
        return "none-val"
    else:
        return "miss"


def ifelif_capture_tail(x):
    """Control 3: value chain then fallback variable."""
    if x == "a":
        return 1
    elif x == 10:
        return 2
    elif x == "b":
        return 3
    else:
        return (x, 0)


def simple_for_loop(items):
    """Control 4: plain for loop with break/continue (no match)."""
    total = 0
    for item in items:
        if item == 0:
            break
        if item == "skip":
            continue
        total += item
    return total


def simple_while_loop(limit):
    """Control 5: plain while loop."""
    n = 0
    hits = []
    while n < limit:
        n += 1
        if n % 3 == 0:
            continue
        if n % 3 == 1:
            hits.append(n)
        else:
            if n > limit - 2:
                break
    return hits


def simple_try(x):
    """Control 6: plain try/except (no match)."""
    try:
        if x == 1:
            return "one"
        elif x == 2:
            return "two"
        else:
            return "other"
    except TypeError:
        return "bad-type"
