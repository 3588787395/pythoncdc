"""rec1_synth g2a: with×match bidirectional host family — match case bodies host with (B93)."""


def g2a_match_hosts_with(v, p):
    match v:
        case [a, b]:
            with open(p) as f:
                return (a, b, f)
        case {'k': kv}:
            with open(p) as g:
                return (kv, g)
        case _:
            return None


def g2a_with_hosts_match(v, p, flag):
    with open(p) as f:
        match v:
            case int(n) if n > 0:
                with open(p) as g:
                    if flag:
                        return (n, f, g)
            case _:
                return -1
    return 0
