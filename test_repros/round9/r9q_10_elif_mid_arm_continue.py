def elif_mid_continue(items, lg):
    for it in items:
        if it == 1:
            lg.info('one')
            continue
        elif it == 2:
            lg.info('two')
        elif it == 3:
            continue
        lg.warn('tail')
