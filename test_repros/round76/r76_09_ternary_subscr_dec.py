# Source Generated with Decompyle++ (Python version)
# File: r76_09_ternary_subscr.pyc (Python 3.11)

def f(df, index_data=False):
    if not df.empty:
        tempdict = OrderedDict()
        index = None
        if index_data:
            index = [df.index[-1]]
        else:
            tempdict['min_time'] = [df.index[-1]]
        tempdict['open'] = [df['open'][0]]
        tempdict['close'] = [df['close'][-1]]
        [1 if df['is_open'] != 0 else 0]
    else:
        return None
