#!/usr/bin/env python3
"""
测试实例8: 方法链式调用
问题：obj.method().attr 可能被错误识别
"""

class Inner:
    def __init__(self):
        self.value = 10

class Outer:
    def get_inner(self):
        return Inner()

def test_method_chain(obj):
    if obj.get_inner().value > 5:
        return "large"
    return "small"
