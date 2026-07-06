#!/usr/bin/env python3
"""
测试实例7: 嵌套if-elif
问题：嵌套结构可能被错误扁平化
"""

def test_nested_if_elif(x, y):
    if x > 0:
        if y > 0:
            return "x>0, y>0"
        elif y < 0:
            return "x>0, y<0"
        else:
            return "x>0, y=0"
    return "x<=0"
