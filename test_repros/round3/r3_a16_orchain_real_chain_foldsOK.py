# Source Generated with Decompyle++ (Python version)
# File: r3_a16_orchain_real_chain_folds.pyc (Python 3.11)

def f(a):
    o = mk(a)
    if o is None:
        return None
    elif is_trade() or o.symbol[:2] in ('11', '12'):
        LOG.info('hit')
    return o.order_id
