"""rec1_synth g3a: B61 deep-host family — mapping **rest capture + fused body-head + guard/assert."""


def g3a_rest_multi(v):
    for x in range(1):
        match v:
            case {'op': op, **rest}:
                if 'tmp' in rest:
                    del rest['tmp']
                return (op, rest)
            case [a, b]:
                return (a + b,)
            case _:
                assert v is not None
                raise TypeError('bad shape')
    return None


def g3a_guard_assert(v, sink):
    match v:
        case int(n) if n > 10:
            assert n < 1000, 'too large'
            sink.append(n * 2)
        case str(s):
            sink.append(s)
    return len(sink)
