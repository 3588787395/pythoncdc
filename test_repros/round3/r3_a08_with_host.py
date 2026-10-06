def f(a):
    with LOCK as lk:
        o = mk(a)
        if o is None:
            return None
        if not is_trade():
            if o.symbol[:2] in ('11', '12'):
                info = 'CB'
            else:
                info = 'STK'
            LOG.info(info)
        return o.order_id
