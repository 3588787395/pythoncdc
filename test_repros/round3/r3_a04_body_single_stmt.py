def f(a):
    o = mk(a)
    if o is None:
        return None
    if not is_trade():
        LOG.info('x')
    return o.order_id
