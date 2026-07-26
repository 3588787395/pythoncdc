# R5 minimal repro: 循环体 STORE_SUBSCR panel[stock]=data 丢失 -> 裸 stock Expr
# 关联缺陷：quotation.pyc load_get_price line 506/513  stock  (R4 残留 #3)
# 触发区域：LOOP / _generate_loop (循环末尾 STORE_SUBSCR 未识别为赋值目标)
# 预期：for stock in panel.items: data = f(stock, panel[stock]); panel[stock] = data
# R5 实际产物：data = f(...); stock   (STORE_SUBSCR 丢失, panel[stock]=data 退化为裸 stock Expr)


def load_get_price(stocks, fq='pre'):
    panel = load_bars(stocks)
    if fq == 'pre':
        exrights = get_exrights(stocks)
        for stock in panel.items:
            data = change_forward(stock, panel[stock], exrights)
            panel[stock] = data
    elif fq == 'post':
        exrights = get_exrights(stocks)
        for stock in panel.items:
            data = change_backward(stock, panel[stock], exrights)
            panel[stock] = data
    return panel
