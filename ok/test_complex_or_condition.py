#!/usr/bin/env python3
"""
最小复现实例：复杂OR条件判断
问题：包含方法链式调用和比较的OR条件被错误反编译
"""
import pandas as pd
import datetime as qdt

def check_condition(data, preindex, n, pandas, qdt):
    """测试复杂OR条件判断"""
    # 这种OR条件可能导致反编译错误
    if data[preindex:n].empty or list(data[preindex:n].index)[-1].tz_localize(None) != pandas.Timestamp(qdt.datetime.strptime(n, '%Y-%m-%d 00:00:00')):
        return True
    return False
