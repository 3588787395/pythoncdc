#!/usr/bin/env python3
"""
测试实例1: if-elif-else链式结构
问题：elif条件可能被错误识别
"""

def test_if_elif_else(x):
    if x > 10:
        return "large"
    elif x > 5:
        return "medium"
    else:
        return "small"
