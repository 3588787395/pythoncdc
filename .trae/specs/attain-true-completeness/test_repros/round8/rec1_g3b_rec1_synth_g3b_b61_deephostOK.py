# Source Generated with Decompyle++ (Python version)
# File: rec1_g3b_rec1_synth_g3b_b61_deephost.pyc (Python 3.11)

__doc__ = 'rec1_synth g3b: B61 deep-host family — rest-capture in with/try hosts (cross variants).'
def g3b_with_rest(v, p):
    with open(p) as f:
        match v:
            case {'op': op, **rest}:
                if 'tmp' in rest:
                    del rest['tmp']
                return (op, rest, f)
                return None(None, None)
            case _:
                assert v is not None
                raise TypeError(v)
def g3b_try_guard_default(v, sink):
    try:
        match v:
            case int(n) if n > 5:
                assert n < 100
                sink.append(n)
            case _:
                pass
    finally:
        sink.append('fin')
    return len(sink)
