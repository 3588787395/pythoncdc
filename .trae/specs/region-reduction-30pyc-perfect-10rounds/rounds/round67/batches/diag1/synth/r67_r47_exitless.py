def u1(o, lg, e):
    while True:
        if len(o.q) > 0:
            try:
                lg.info(f"g {o.a} {'P' if o.b == e else 'Q'} z")
            except BaseException:
                lg.error('e')
        time.sleep(0.001)


def u2(o, lg, e):
    while True:
        try:
            lg.info(f"g {o.a} {'P' if o.b == e else 'Q'} z")
        except BaseException:
            lg.error('e')
        time.sleep(0.001)


def u3(o, lg, e):
    while True:
        try:
            lg.info('g {} {}'.format(o.a, 'P' if o.b == e else 'Q'))
        except BaseException:
            lg.error('e')
        time.sleep(0.001)


def u4(o, lg, e):
    while True:
        try:
            t = 'P' if o.b == e else 'Q'
            lg.info(f"g {t}")
        except BaseException:
            lg.error('e')
    return None


def u5(o, lg, e):
    while len(o.q) > 0:
        try:
            lg.info(f"g {o.a} {'P' if o.b == e else 'Q'} z")
        except BaseException:
            lg.error('e')
        time.sleep(0.001)
    return None
