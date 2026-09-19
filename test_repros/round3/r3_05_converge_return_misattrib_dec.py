# Source Generated with Decompyle++ (Python version)
# File: r3_05_converge_return_misattrib.pyc (Python 3.11)

__doc__ = """R3-E: 多分支汇聚到函数尾 return 的结构被改写 —— 顶层 return 被归属为内层 else 的提前 return,
其余路径落到隐式 return None; 另有 ~ & ~ 下标过滤语句丢失变体。
对照 quote.pyc fill_minute_or_day_blank: orig O3/O53/O131 三条 POP_JUMP_FORWARD_IF_FALSE
全部指向函数尾 `return klines`; 反编译后 else: return klines, 顶层 return 丢失。"""
def fill_minute_or_day_blank(self, klines, nowstart, nowend, typet, stocks, forward='pre'):
    if nowend >= nowstart:
        code = stocks.split('.')[0]
        suffix = stocks.split('.')[1]
        suffix = 'T.' + suffix if suffix == 'CCFX' and code[:1] == 'T' else suffix
        source_start = nowstart
        source_end = nowend
        dts = self.get_minute_or_day_fill_time(suffix, typet, nowstart, nowend)
        if len(dts) > 0:
            source_start = qdt.datetime.strptime(source_start[:8] + (len(source_start[8:]) == 4 and source_start[8:] or '0000'), '%Y%m%d%H%M')
            source_end = qdt.datetime.strptime(source_end[:8] + (len(source_end[8:]) == 4 and source_end[8:] or '1530'), '%Y%m%d%H%M')
            dts = dts[~(dts.index < source_start) & ~(dts.index > source_end)]
            if len(dts) > 0:
                dts = dts.index
                if forward == 'back':
                    temp_close = numpy.array([klines['close'][-1]] * len(dts))
                    temp_value = numpy.array([0] * len(dts))
                    klines_back = pandas.DataFrame({'open': temp_close, 'close': temp_close}, index=dts)
                    klines = pandas.concat([klines, klines_back])
                else:
                    temp_value = numpy.array([0] * len(dts))
                    klines_pre = pandas.DataFrame({'open': temp_value, 'close': temp_value}, index=dts)
                    klines = pandas.concat([klines_pre, klines])
            else:
                return klines
