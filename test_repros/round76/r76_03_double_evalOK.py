# Source Generated with Decompyle++ (Python version)
# File: r76_03_double_eval.pyc (Python 3.11)

import os
DATAFILE = '/tmp/data.bin'
def f(stocks, typet):
    log('load_bars', stocks, typet)
    data = OrderedDict()
    retpanel = Panel()
    if os.path.exists(DATAFILE) and typet == 6:
        if isinstance(stocks, str):
            stocks = [stocks]
        loadmod = reload('load_daily')
        if data.get('date') != 'today':
            reload(loadmod)
            data['date'] = 'today'
        daily = loadmod.cshare
        for s in stocks:
            source = daily[s]
            data[s] = source
    return retpanel
