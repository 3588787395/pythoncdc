#!/usr/bin/env python3
"""测试DataFrame构造"""
import pandas as pd

def create_dataframe(redata, columns):
    """DataFrame构造"""
    return pd.DataFrame([redata], columns=columns)
