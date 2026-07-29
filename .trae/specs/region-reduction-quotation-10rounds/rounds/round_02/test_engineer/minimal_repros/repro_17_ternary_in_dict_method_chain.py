"""repro_17: 三元表达式作为字典值 + 前序方法调用（fill_minute_or_day_blank 变体）。

原始 fill_minute_or_day_blank 的 else 分支含三元与 dict 构造混合：
    klines_back = pandas.DataFrame({'open': temp_close, 'close': temp_close, ...}, index=dts)
反编译器把三元 `suffix = 'T.' + suffix if suffix == 'CCFX' and code[:1] == 'T' else suffix`
与前序 `code = stocks.split('.')[0]` 合并。本 repro 聚焦 Ternary 作为前置语句归约缺陷。
"""
import numpy
import pandas


def fill_blank(klines, nowstart, nowend, typet, stocks, forward='pre'):
    if nowend >= nowstart:
        code = stocks.split('.')[0]
        suffix = 'T.' + suffix if suffix == 'CCFX' and code[:1] == 'T' else suffix
        if len(dts) > 0:
            temp_close = numpy.array([klines['close'][-1]] * len(dts))
            temp_value = numpy.array([numpy.nan] * len(dts))
            if forward == 'back':
                klines_back = pandas.DataFrame({'open': temp_close, 'close': temp_close, 'high': temp_close, 'low': temp_close, 'volume': temp_value, 'money': temp_value}, index=dts)
                klines = pandas.concat([klines, klines_back])
            else:
                klines_pre = pandas.DataFrame({'open': temp_value, 'close': temp_value, 'high': temp_value, 'low': temp_value, 'volume': temp_value, 'money': temp_value}, index=dts)
                klines = pandas.concat([klines_pre, klines], sort=True)
    return klines
