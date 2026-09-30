# -*- coding: utf-8 -*-
# R76-A1 复现（对照 Quote.get_price）：if 守卫（单操作数 is not None）的前置块
# 含多条语句；守卫体含 if + assert + for。预期缺陷：守卫物化为裸表达式
# `fields is not None`，体语句变为无条件执行。
def f(fields, frequency):
    log('enter', frequency)
    candle = None
    check(frequency)
    if fields is not None:
        if not isinstance(fields, list):
            error('get_price bad fields 1')
            error('get_price bad fields 2')
        assert isinstance(fields, list), 'fields must be list'
        for field in fields:
            if field not in ('open', 'close'):
                error('unknown field')
                raise AssertionError('unknown field')
    if frequency.find('w') > -1:
        candle = 7
    return candle
