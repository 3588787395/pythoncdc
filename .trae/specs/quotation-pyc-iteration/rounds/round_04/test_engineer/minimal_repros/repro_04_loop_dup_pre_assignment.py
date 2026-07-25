# R4 minimal repro: 循环前置赋值重复发射
# 关联缺陷：新发现 (R4 新增, load_bars_from_hundsun source_end = end[8:] or '1530' 出现 2 次)
# 触发区域：LOOP
# 预期：source_end = end[8:] or '1530' 仅出现 1 次
# R4 实际产物：source_end = end[8:] or '1530' 出现 2 次 (for_iter_setup pre_stmts 重复发射)
def load_bars_from_hundsun(stocks, typet, start, end):
    global is_utc
    source_start = start[8:] or '0900'
    source_end = end[8:] or '1530'
    if isinstance(stocks, str):
        stocks = [stocks]
    dailypanel = load_daily_panel(stocks, start, end)
    diffset = set(stocks) - set(dailypanel.items)
    if len(diffset) < len(stocks):
        sectionstocks = list(set(stocks).intersection(set(dailypanel.items)))
        dailypanel = dailypanel.ix[:, source_start:source_end]
        retpanel = dailypanel.ix[sectionstocks, :]
        stocks = list(diffset)
    retpanel = None
    for stock in stocks:
        klines = load_minute_or_day_kline(stock, typet, start, end)
        if klines is not None and 'price' not in klines:
            klines.insert(5, 'price', klines['close'])
    return retpanel
