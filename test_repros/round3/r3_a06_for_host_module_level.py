for a in SEQ:
    o = mk(a)
    if o is None:
        continue
    if not is_trade():
        if o.symbol[:2] in ('11', '12'):
            info = 'CB'
        else:
            info = 'STK'
        LOG.info(info)
    LOG.info(o.order_id)
