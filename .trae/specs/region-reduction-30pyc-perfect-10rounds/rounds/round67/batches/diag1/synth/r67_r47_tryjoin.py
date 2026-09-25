def v1(o, lg, e):
    try:
        lg.info(f"g {o.a} {'P' if o.b == e else 'Q'} z")
        return o.a
    except Exception:
        lg.error('e')


def v2(o, lg, e):
    lg.info(f"g {o.a} {'P' if o.b == e else 'Q'} z")
    return o.a


def v3(o, lg, e):
    try:
        lg.info('g {} {}'.format(o.a, 'P' if o.b == e else 'Q'))
        return o.a
    except Exception:
        lg.error('e')


def v4(o, lg, e):
    try:
        t = 'P' if o.b == e else 'Q'
        lg.info(f"g {t}")
        return o.a
    except Exception:
        lg.error('e')


def v5(o, lg, e, f):
    try:
        lg.info('g {s} {p}'.format(s='P' if o.b == e else 'Q', p='U' if o.c == f else 'V'))
        return o.a
    except Exception:
        lg.error('e')


def v6(o, lg, e):
    try:
        lg.info(_('g %s ') % o.a)
        lg.info(f"x {o.a} {'P' if o.b == e else 'Q'} y")
        return o.a
    except Exception:
        lg.error('e')


def v7(o, lg, e):
    try:
        lg.info(f"x {o.a} {'P' if o.b == e else 'Q'} y")
    except Exception:
        lg.error('e')
    return o.a
