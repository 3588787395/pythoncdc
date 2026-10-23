# Source Generated with Decompyle++ (Python version)
# File: rec1_synth_g1a_guard_depth.pyc (Python 3.11)

__doc__ = 'rec1_synth g1a: match×guard depth family — or-guard chains at depth + assert-in-case discrimination (B61a).'
def g1_for_with_or_guard(v, flag, xs, sink):
    for x in xs:
        with open('p') as f:
            match v:
                case int(n) if n > 0 or flag:
                    assert n < 1000
                    sink.append(n)
                case int(n):
                    sink.append(-n)
                case _:
                    sink.append(0)
    return len(sink)
def g1_if_or_chain3_assert(v, flag, sink):
    if flag:
        match v:
            case int(n) if n > 0 or n < -10 or flag:
                assert n < 500, 'large'
                sink.append(n)
            case _:
                sink.append(0)
    return 1
