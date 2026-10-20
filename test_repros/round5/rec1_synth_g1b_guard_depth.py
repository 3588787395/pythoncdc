"""rec1_synth g1b: match×guard depth family — guards in while/try hosts (cross variants)."""


def g1b_while_guard(v, flag, sink):
    while flag:
        match v:
            case str(s) if len(s) > 2 or flag:
                assert s
                sink.append(s)
                flag = False
            case _:
                sink.append(0)
                flag = False
    return len(sink)


def g1b_try_guard(v, sink):
    try:
        match v:
            case int(n) if n % 2 == 0:
                assert n > 0, 'positive'
                sink.append('even')
            case int(n):
                sink.append('odd')
            case _:
                sink.append('other')
    finally:
        sink.append('fin')
    return len(sink)
