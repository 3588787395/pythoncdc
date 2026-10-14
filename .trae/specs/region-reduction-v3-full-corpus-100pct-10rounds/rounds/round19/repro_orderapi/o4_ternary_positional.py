def f(order_, log):
    log.info('buy' if order_.dir.value.upper() == 'BUY' else 'sell')
