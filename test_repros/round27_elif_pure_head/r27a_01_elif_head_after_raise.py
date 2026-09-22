def case_elif_head_after_raise(meta, proxy, to_date):
    if meta['start_date'] != meta['want_date']:
        raise RuntimeError('start mismatch %s' % meta['start_date'])
    if meta['last_dt'] is None:
        return False
    if meta['last_dt'] > meta['end_date']:
        raise RuntimeError('end mismatch %s' % meta['end_date'])
    if meta['last_dt'] == meta['end_date']:
        return False
    nxt = proxy.get_next(meta['last_dt'])
    nxt = to_date(nxt)
    if nxt > meta['end_date']:
        return False
    return True


def control_first_arm_returns(meta):
    if meta['start_date'] != meta['want_date']:
        return None
    if meta['last_dt'] is None:
        return False
    if meta['last_dt'] > meta['end_date']:
        raise RuntimeError('end mismatch %s' % meta['end_date'])
    if meta['last_dt'] == meta['end_date']:
        return False
    return True


def control_head_carries_own_statement(meta):
    if meta['x'] != meta['y']:
        raise RuntimeError('xy')
    meta['z'] = meta['x']
    if meta['z'] > meta['w']:
        return 1
    return 2
