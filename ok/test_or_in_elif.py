#!/usr/bin/env python3
"""测试elif中的OR条件 - quote.pyc中的实际问题"""
import pandas as pd
import datetime as qdt

def process_data(data, preindex, n, series):
    """elif中的OR条件测试"""
    tmpdata = None
    if preindex is None:
        tmpdata = data[:n][:-1]
    elif data[preindex:n].empty or list(data[preindex:n].index)[-1].tz_localize(None) != pd.Timestamp(qdt.datetime.strptime(n, '%Y-%m-%d 00:00:00')):
        return True
    return False
