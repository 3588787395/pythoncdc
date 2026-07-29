"""repro_07: if/else 的 else 分支 + 三元/BoolOp 混合丢失（fill_minute_or_day_blank）。

原始 fill_minute_or_day_blank 中 `if nowend >= nowstart:` 的 else 分支（含
numpy.array([numpy.nan] * len(dts)) + pandas.DataFrame + pandas.concat）整体丢失，
POP_JUMP_FORWARD_IF_FALSE 目标 1206 被收敛为 946。else 分支含 `forward == 'back'` 三元与
`and/or` 短路混合。本 repro 聚焦 Ternary + Conditional else 分支归约缺陷。
"""
import numpy
import pandas


def fill_blank(klines, nowstart, nowend, typet, stocks, forward='pre'):
    if nowend >= nowstart:
        code = stocks.split('.')[0]
        if len(dts) > 0:
            temp_value = numpy.array([numpy.nan] * len(dts))
            if forward == 'back':
                temp_close = numpy.array([klines['close'][-1]] * len(dts))
                klines_back = pandas.DataFrame({'open': temp_close, 'close': temp_close}, index=dts)
                klines = pandas.concat([klines, klines_back])
            else:
                klines_pre = pandas.DataFrame({'open': temp_value, 'close': temp_value}, index=dts)
                klines = pandas.concat([klines_pre, klines], sort=True)
    else:
        temp_value = numpy.array([numpy.nan] * len(dts))
        klines_pre = pandas.DataFrame({'open': temp_value, 'close': temp_value}, index=dts)
        klines = pandas.concat([klines_pre, klines], sort=True)
    return klines
