#!/usr/bin/env python3
"""
测试实例3: 属性访问作为条件
问题：obj.attr 条件可能被错误识别
"""

class Data:
    def __init__(self):
        self.empty = True
        self.value = None

def test_attr_condition(data):
    if data.empty:
        return "empty"
    return "not empty"
