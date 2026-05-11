#!/usr/bin/env python3
"""
测试实例：属性访问作为if条件
问题：obj.attr 条件可能被错误识别为 True
"""

class Data:
    def __init__(self):
        self.empty = False

def test_attr_if(data):
    if data.empty:
        return "empty"
    return "not empty"
