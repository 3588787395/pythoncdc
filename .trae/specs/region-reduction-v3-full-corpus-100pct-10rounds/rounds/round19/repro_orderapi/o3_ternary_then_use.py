def f(order_, log):
    side = ('buy' if order_.dir.value.upper() == 'BUY' else 'sell')
    log.info('a{side}b'.format(side=side))
