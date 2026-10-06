# Source Generated with Decompyle++ (Python version)
# File: r3_a06_for_host_module_level.pyc (Python 3.11)

for a in SEQ:
    o = mk(a)
    if o is None:
        continue
    elif not is_trade():
        if o.symbol[:2] in ('11', '12'):
            info = 'CB'
        else:
            info = 'STK'
        LOG.info(info)
    LOG.info(o.order_id)
