def region_mean_repro(value_array, days_start, days_end, user_log):
    """witness 1: if/elif chain whose arms all return, plus a post-chain `return False`."""
    if len(value_array) < max(days_start, days_end):
        user_log.info('区间均值状态判断入参序列数据长度不足')
        return None
    elif sum(value_array[-days_start:]) <= value_array[-1] <= sum(value_array[-days_end:]):
        return True
    return False


def arm_continuation_repro(asset, amount, close_today, strategy_log):
    """witness 2: 3-arm chain; middle arm jumps into a shared post-chain tail, last arm has a
    continuation block of its own before that same tail (order_api.buy_close shape)."""
    if asset.type != 2:
        strategy_log.warning('%s非期货标的, 委托取消' % asset)
        return None
    elif asset.exchange == 'XSGE':
        if close_today:
            direction = 1
            current = asset.sell_today_amount
            if current == 0:
                strategy_log.warning('今仓持仓数量为0, 无法平仓, 委托取消')
                return None
        else:
            direction = 2
            current = asset.sell_amount
    elif close_today:
        strategy_log.warning('不支持平今仓方式')
        direction = 2
        current = asset.sell_amount
    if current == 0:
        strategy_log.warning('持仓数量为0, 无法平仓, 委托取消')
        return None
    elif current < amount:
        strategy_log.warning('持仓数量为%d, 调整' % current)
        amount = current
    return (asset, amount, direction)


def no_tail_repro(asset, close_today, strategy_log):
    """control: chain with no post-chain statement at all (arms end in return / fall off)."""
    if asset.type != 2:
        strategy_log.warning('bad')
        return None
    elif close_today:
        strategy_log.warning('no tail here')
        return 1
    return 2
