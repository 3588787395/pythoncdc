def w(a, b, c, d, log):
    log.info('id {i} sym {s} side {side} op {oper}'.format(i=a, s=b, side='BUY' if c else 'SELL', oper='OPEN' if d else 'CLOSE'))
    return a
