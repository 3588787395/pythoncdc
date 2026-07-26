# R5 minimal repro: 函数体含 for+if+多层嵌套时严重退化 (R4 残留 #5 同源, fill_minute_or_day_blank 整体 -> pass)
# 关联缺陷：quotation.pyc fill_minute_or_day_blank line 305-306  def f(...): pass (R4 残留 #5)
# 触发区域：LOOP + IF 嵌套 / _generate_region (函数体含 for+if+boolop+嵌套赋值时控制流被破坏)
# 预期：if klines is None or len(klines)==0: return klines;  if typet==6: for stock: ...; return klines
# R5 实际产物：
#   if klines is not None:                       <- `or` boolop 条件被反转为 is not None
#       if len(klines)==0: ... elif typet==6:
#           stocks                               <- 裸 Name (赋值丢失)
#           for stock: ...: filled = filled[idx >= nowstart & idx <= nowend]  <- 括号丢失 + klines[stock]=filled 丢失
#           else: return klines                  <- spurious for-else


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
