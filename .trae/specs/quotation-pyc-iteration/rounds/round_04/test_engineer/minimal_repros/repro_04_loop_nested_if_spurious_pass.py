# R4 minimal repro: 循环内嵌套 if 后产生 spurious if + pass
# 关联缺陷：新发现 (R4 新增, load_bars_from_hundsun: if len(end[8:]) == 4: pass)
# 触发区域：LOOP + IF
# 预期：循环内 if 条件成立时执行赋值
# R4 实际产物：if cond: pass (条件保留但语句体丢失)
def process_klines(klines, end, typet):
    for stock in klines:
        stock_klines = klines[stock]
        if stock_klines is None:
            continue
        if len(end[8:]) == 4:
            stock_klines['endtime'] = end[8:] + '00'
        if typet == 13:
            stock_klines = stock_klines.tz_convert('UTC')
        klines[stock] = stock_klines
    return klines
