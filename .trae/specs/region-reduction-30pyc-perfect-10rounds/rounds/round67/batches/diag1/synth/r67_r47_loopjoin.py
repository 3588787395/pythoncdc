def w1(o, lg, e):
    while len(o.q) > 0:
        try:
            lg.info(f"g {o.a} {'P' if o.b == e else 'Q'} z")
            return o.a
        except Exception:
            lg.error('e')
    return None


def w2(o, lg, e):
    while len(o.q) > 0:
        lg.info(f"g {o.a} {'P' if o.b == e else 'Q'} z")
        return o.a
    return None


def w3(o, lg, e):
    while len(o.q) > 0:
        try:
            lg.info('g {} {}'.format(o.a, 'P' if o.b == e else 'Q'))
            return o.a
        except Exception:
            lg.error('e')
    return None


def w4(o, lg, e):
    while len(o.q) > 0:
        try:
            t = 'P' if o.b == e else 'Q'
            lg.info(f"g {t}")
            return o.a
        except Exception:
            lg.error('e')
    return None


def w5(o, lg, e):
    while len(o.q) > 0:
        try:
            lg.info(f"g {o.a} {'P' if o.b == e else 'Q'} z")
        except Exception:
            lg.error('e')
        lg.warn('after')
    return None


def w6(o, lg, e):
    for x in o.q:
        try:
            lg.info(f"g {x.a} {'P' if x.b == e else 'Q'} z")
            return x.a
        except Exception:
            lg.error('e')
    return None
