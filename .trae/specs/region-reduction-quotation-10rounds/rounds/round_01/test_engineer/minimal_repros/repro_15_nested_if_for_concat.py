"""repro_15: 嵌套 if + for + append + 尾部 concat（fill_minute_or_day_blank 变体）。

复现原始字节码结构：if len(dts) > 0: 内嵌 if forward == 'back': ... else: ...
每个分支含 numpy.array + pandas.DataFrame + pandas.concat 多步构造。
反编译器丢失 else 分支（少指令）。
对应 _identify_conditional_regions / _generate_if 嵌套 if/else 归约。
"""
import numpy
import pandas


def fill_blank(dts, forward, klines):
    if len(dts) > 0:
        if forward == 'back':
            temp_close = numpy.array([klines['close'][-1]] * len(dts))
            temp_value = numpy.array([numpy.nan] * len(dts))
            klines_back = pandas.DataFrame({'open': temp_close, 'close': temp_close, 'high': temp_close, 'low': temp_close, 'volume': temp_value, 'money': temp_value}, index=dts)
            klines = pandas.concat([klines, klines_back])
        else:
            temp_value = numpy.array([numpy.nan] * len(dts))
            klines_pre = pandas.DataFrame({'open': temp_value, 'close': temp_value, 'high': temp_value, 'low': temp_value, 'volume': temp_value, 'money': temp_value}, index=dts)
            klines = pandas.concat([klines_pre, klines], sort=True)
    return klines
