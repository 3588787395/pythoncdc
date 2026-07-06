#!/usr/bin/env python3
"""
测试实例2: if语句内嵌套if
问题：嵌套if的条件可能被错误合并
"""

def test_nested_if(x, y):
    if x > 0:
        if y > 0:
            return "both positive"
        return "x positive"
    return "x negative"
