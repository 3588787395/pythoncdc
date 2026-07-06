#!/usr/bin/env python3
"""测试复杂OR条件 - 问题：短路求值被错误分解"""
import pandas as pd
import datetime as qdt

def check_or_condition(data, preindex, n, pandas, qdt):
    """OR条件短路求值"""
    if data[preindex:n].empty or list(data[preindex:n].index)[-1].tz_localize(None) != pandas.Timestamp(qdt.datetime.strptime(n, '%Y-%m-%d 00:00:00')):
        return True
    return False
