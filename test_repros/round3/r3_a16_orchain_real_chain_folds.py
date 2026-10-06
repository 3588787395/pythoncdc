def f(a):
    o = mk(a)
    if o is None:
        return None
    if is_trade() or o.symbol[:2] in ('11', '12'):
        LOG.info('hit')
    return o.order_id
