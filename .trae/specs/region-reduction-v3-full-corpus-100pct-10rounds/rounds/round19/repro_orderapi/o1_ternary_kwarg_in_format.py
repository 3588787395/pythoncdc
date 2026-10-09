def f(order_, log):
    log.info('a{side}b'.format(side=('buy' if order_.dir.value.upper() == 'BUY' else 'sell')))
