#!/usr/bin/env python3
"""
测试实例10: 复杂嵌套控制流
问题：多层嵌套可能被错误处理
"""

def test_complex_nested(a, b, c, d):
    if a > 0:
        if b > 0:
            if c > 0:
                if d > 0:
                    return "all positive"
                return "a,b,c>0, d<=0"
            return "a,b>0, c<=0"
        return "a>0, b<=0"
    return "a<=0"
