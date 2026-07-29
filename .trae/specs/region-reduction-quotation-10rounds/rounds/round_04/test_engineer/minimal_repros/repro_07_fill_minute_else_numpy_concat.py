"""repro_07: else 分支 `numpy.array` + `pandas.DataFrame` + `pandas.concat` 丢失（fill_minute_or_day_blank）。

fill_minute_or_day_blank 的 -42 指令差异源于 else 分支（numpy.array + pandas.concat）丢失。
镜像实际 CFG：
  - if nowend >= nowstart: ... else: klines = pandas.concat([klines_pre, klines])
  - else 分支含 numpy.array(numpy.nan) + pandas.DataFrame + pandas.concat
"""


def fill_minute_or_day_blank_repro(nowend, nowstart, stocks, dts):
    if nowend >= nowstart:
        code = stocks.split('.')[0]
        klines = []
        for dt in dts:
            if dt not in klines:
                klines.append(dt)
        klines_back = klines
    else:
        temp_value = numpy.array([numpy.nan] * len(dts))
        klines_pre = pandas.DataFrame({'open': temp_value, 'close': temp_value, 'high': temp_value, 'low': temp_value, 'volume': temp_value, 'money': temp_value}, index=dts)
        klines = pandas.concat([klines_pre, klines])
    return klines
