# -*- coding: utf-8 -*-
# R76-A2 复现（对照 Quote.load_bars_from_hundsun）：前置多语句块（日志+两个
# 赋值）尾部跟 and 链首操作数 `os.path.exists(...)`，体含 if/for。
# 预期缺陷：操作数既物化为裸表达式又保留在条件里（双重求值）。
import os

DATAFILE = '/tmp/data.bin'

def f(stocks, typet):
    log('load_bars', stocks, typet)
    data = OrderedDict()
    retpanel = Panel()
    if os.path.exists(DATAFILE) and typet == 6:
        if isinstance(stocks, str):
            stocks = [stocks]
        loadmod = reload('load_daily')
        if data.get('date') != 'today':
            reload(loadmod)
            data['date'] = 'today'
        daily = loadmod.cshare
        for s in stocks:
            source = daily[s]
            data[s] = source
    return retpanel
