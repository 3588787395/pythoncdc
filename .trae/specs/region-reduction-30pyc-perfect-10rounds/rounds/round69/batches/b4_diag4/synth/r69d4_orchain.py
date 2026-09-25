def v1(order_, flag, log, x):
    if order_ is None:
        return None
    if flag:
        return 'T'
    log.info('订单 {} {}'.format(order_.oid, '买入' if x == 1 else '卖出'))


def v2(order_, flag, log, x):
    try:
        if order_ is None:
            return None
        if flag:
            return 'T'
        log.info('订单 {} {}'.format(order_.oid, '买入' if x == 1 else '卖出'))
    except Exception:
        pass


def v3(order_, flag, log, x):
    if order_ is None:
        return None
    elif flag:
        return 'T'
    log.info('订单 {} {}'.format(order_.oid, '买入' if x == 1 else '卖出'))


def v4(order_, flag, log, x):
    if order_ is None:
        return None
    if flag:
        return 'T'
    else:
        log.info('订单 {} {}'.format(order_.oid, '买入' if x == 1 else '卖出'))
    return 0


def v5(order_, flag, log, x, side):
    if order_ is None:
        return None
    if flag:
        return 'T'
    log.info('订单 {} {}'.format(order_.oid, side.upper() == 'BUY' and '买入' or '卖出'))
