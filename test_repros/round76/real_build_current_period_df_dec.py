# Source Generated with Decompyle++ (Python version)
# File: real_build_current_period_df.pyc (Python 3.11)

def build_current_period_df(self, nowdataframe, index_data):
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
