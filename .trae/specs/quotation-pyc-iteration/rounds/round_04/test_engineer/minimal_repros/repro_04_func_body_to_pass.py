# R4 minimal repro: 整个函数体被替换为 pass
# 关联缺陷：新发现 (R4 新增, fill_minute_or_day_blank orig=244 new=3)
# 触发区域：LOOP + IF (函数体含 for + if + 多层嵌套)
# 预期：完整函数体含 for + if + 复杂赋值
# R4 实际产物：def f(...): pass
def fill_minute_or_day_blank(klines, nowstart, nowend, typet, stocks, forward='pre'):
    if klines is None or len(klines) == 0:
        return klines
    if typet == 6:
        for stock in stocks:
            stock_klines = klines[stock]
            if stock_klines is None:
                continue
            if forward == 'pre':
                filled = stock_klines.fillna(method='ffill')
            else:
                filled = stock_klines.fillna(method='bfill')
            if len(filled) > 0:
                filled = filled[(filled.index >= nowstart) & (filled.index <= nowend)]
                klines[stock] = filled
            else:
                klines[stock] = None
    return klines
