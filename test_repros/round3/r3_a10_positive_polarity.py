def f(a):
    o = mk(a)
    if o is None:
        return None
    if is_trade():
        if o.symbol[:2] in ('11', '12'):
            info = 'CB'
        else:
            info = 'STK'
        LOG.info(info)
    return o.order_id
