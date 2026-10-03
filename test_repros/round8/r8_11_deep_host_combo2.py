"""R8-11 Deep host combos round 2: while-else raise / try full sections / nested try del / with multi / match guard assert-pass."""


def r8_dh2_while_else_raise(n, lim):
    while n < lim:
        n += 1
    else:
        if n > 100:
            raise OverflowError("runaway")
    return n


def r8_dh2_try_full_sections(xs, i):
    r = None
    try:
        r = xs[i]
    except IndexError:
        r = "fallback"
    else:
        r = r * 2
    finally:
        probe = getattr(r, "bit_length", None)
    return r


def r8_dh2_nested_try_del(xs):
    out = []
    for i in range(len(xs)):
        try:
            if xs[i] < 0:
                del xs[i]
                out.append(-1)
        except IndexError:
            raise
    return out


def r8_dh2_with_multi(a, b):
    with open(a) as fa, open(b) as fb:
        x = fa.read(1)
        y = fb.read(1)
    return x, y


def r8_dh2_match_guard(x):
    match x:
        case int() as v if v > 10:
            assert v < 1000, "too large"
            return v * 2
        case str() as s:
            return len(s)
        case _:
            pass
    return None
