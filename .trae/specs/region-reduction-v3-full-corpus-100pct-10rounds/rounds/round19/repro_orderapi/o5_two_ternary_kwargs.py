def f(order_, log):
    log.info('a{side}{op}b'.format(side=('buy' if order_.d.value.upper() == 'BUY' else 'sell'), op=('open' if order_.k == 1 else 'close')))
