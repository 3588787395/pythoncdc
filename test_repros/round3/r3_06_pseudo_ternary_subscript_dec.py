# Source Generated with Decompyle++ (Python version)
# File: r3_06_pseudo_ternary_subscript.pyc (Python 3.11)

__doc__ = """R3-F: 下标赋值 + 列表三元值 + 尾随语句 —— 伪三元合并、赋值目标丢失、后续语句被吞。
对照 quote.pyc build_current_period_df 尾部:
    tempdict['is_open'] = [1] if ...['is_open'] != 0 else [0]
    tmp = pandas.DataFrame(tempdict, index=index)
    return tmp
反编译输出只剩 `[1 if ... else 0]` 裸表达式 + 隐式 return None。"""
def build_current_period_df(self, nowdataframe, index_data=False):
    if not nowdataframe.empty:
        tempdict = OrderedDict()
        index = None
        if index_data:
            index = [nowdataframe.index[-1]]
        else:
            tempdict['min_time'] = [nowdataframe.index[-1]]
        tempdict['open'] = [nowdataframe['open'][0]]
        tempdict['close'] = [nowdataframe['close'][-1]]
        tempdict['high'] = [nowdataframe['high'].max()]
        tempdict['low'] = [nowdataframe['low'].min()]
        nowdataframe.loc['Row_sum'] = nowdataframe.apply(lambda x: x.sum())
        tempdict['volume'] = [nowdataframe.loc['Row_sum']['volume']]
        tempdict['money'] = [nowdataframe.loc['Row_sum']['money']]
        [1 if nowdataframe.loc['Row_sum']['is_open'] != 0 else 0]
    else:
        return None
