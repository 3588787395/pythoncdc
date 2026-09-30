# Source Generated with Decompyle++ (Python version)
# File: real_load_get_price.pyc (Python 3.11)

def load_get_price(self, stocks, typet, start, end, fq):
    self.log.quote.debug(f'调用函数load_get_price，参数为：stocks={stocks[:10]!s}等{len(stocks) if isinstance(stocks, list) else 1!s}只代码,typet={typet!s},start={start!s},end={end!s},fq={fq!s}')
    panel = self.load_bars_from_hundsun(stocks, typet, start, end)
    if len(panel.major_axis) != 0:
        if is_utc == '0':
            if typet in (1, 2, 3, 4, 5, 13):
                panel.major_axis = panel.major_axis.tz_convert('Asia/Shanghai')
        elif typet in (1, 2, 3, 4, 5, 13):
            panel.major_axis = panel.major_axis.tz_localize('UTC').tz_convert('Asia/Shanghai')
    panel.major_axis = panel.major_axis.tz_localize(None)
    if fq == 'pre':
        exrights_data = self.get_exrights_data(stocks, start)
        for stock in panel.items:
            data = self.change_his_to_forward(stock, panel[stock], exrights_data, start, end)
            panel[stock] = data
    elif fq == 'post':
        exrights_data = self.get_exrights_data(stocks, start)
        for stock in panel.items:
            data = self.change_his_to_backward(stock, panel[stock], exrights_data, start, end)
            panel[stock] = data
    else:
        panel = panel
    if isinstance(stocks, str):
        rdata = panel[stocks]
    else:
        rdata = panel
    return rdata
