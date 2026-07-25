# R4 minimal repro: 循环体 STORE_SUBSCR panel[stock]=data 丢失 + 裸 stock Expr
# 关联缺陷：repro_03_loop_store_subscr_to_annotation (P2 残留) + repro_03_loop_bare_name_and_dup (R3 修复在 quotation.pyc 退化)
# 触发区域：LOOP
# 预期：for stock in panel.items: data = f(stock, panel[stock], ...); panel[stock] = data
# R4 实际产物：data = f(...); stock   (STORE_SUBSCR 丢失 + 裸 stock Expr)
def load_get_price(stocks, fq=None):
    panel = load_bars_from_hundsun(stocks)
    if fq == 'pre':
        exrights_data = get_exrights_data(stocks)
        for stock in panel.items:
            data = change_his_to_forward(stock, panel[stock], exrights_data)
            panel[stock] = data
    elif fq == 'post':
        exrights_data = get_exrights_data(stocks)
        for stock in panel.items:
            data = change_his_to_backward(stock, panel[stock], exrights_data)
            panel[stock] = data
    return panel
