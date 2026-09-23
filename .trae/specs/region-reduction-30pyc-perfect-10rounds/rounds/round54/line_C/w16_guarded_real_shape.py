def w(a, b, c, d, e, log, g):
    if not g():
        log.info('id {i} sym {s} side {side} oper {oper} share {sh} h {h}'.format(i=a, s=b, side='BUY' if c else 'SELL', oper='OPEN' if d else 'CLOSE', sh=e, h='SPEC' if e else 'HEDGE'))
    return a
