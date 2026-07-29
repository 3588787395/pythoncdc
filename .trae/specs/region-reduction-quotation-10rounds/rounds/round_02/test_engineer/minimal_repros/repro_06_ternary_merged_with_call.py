"""repro_06: 三元表达式与前序方法调用合并（fill_minute_or_day_blank 模式）。

原始 fill_minute_or_day_blank：
    code = stocks.split('.')[0]
    suffix = 'T.' + suffix if suffix == 'CCFX' and code[:1] == 'T' else suffix
反编译器把三元表达式合并进 stocks.split(...) 的参数，产生错误源码：
    suffix = stocks.split('T.' + suffix if suffix == 'CCFX' and code[:1] == 'T' else suffix)
本 repro 聚焦 Ternary 与前序 STORE_FAST/method call 归约交互缺陷。
"""


def fill_blank(klines, nowstart, nowend, typet, stocks, forward='pre'):
    if nowend >= nowstart:
        code = stocks.split('.')[0]
        suffix = 'T.' + suffix if suffix == 'CCFX' and code[:1] == 'T' else suffix
        if len(dts) > 0:
            temp_value = numpy.array([numpy.nan] * len(dts))
            klines_back = pandas.DataFrame({'open': temp_value, 'close': temp_value}, index=dts)
            klines = pandas.concat([klines, klines_back])
    return klines
