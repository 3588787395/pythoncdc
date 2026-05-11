#!/usr/bin/env python3
"""
测试实例4: len()比较
问题：len(x) > n 可能被错误识别为常量
"""

def test_len_comparison(s):
    if len(s) > 8:
        return s[:8]
    return s
