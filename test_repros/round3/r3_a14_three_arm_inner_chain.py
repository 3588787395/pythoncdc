def f(a):
    o = mk(a)
    if o is None:
        return None
    if not is_trade():
        if o.symbol[:2] in ('11', '12'):
            info = 'CB'
        elif o.symbol[:2] in ('13',):
            info = 'CB2'
        else:
            info = 'STK'
        LOG.info(info)
    return o.order_id
