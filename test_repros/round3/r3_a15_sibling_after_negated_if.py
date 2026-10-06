def f(a):
    o = mk(a)
    if o is None:
        return None
    if not is_trade():
        if o.symbol[:2] in ('11', '12'):
            info = 'CB'
        else:
            info = 'STK'
        LOG.info(info)
    o.used = True
    return o.order_id
