#!/usr/bin/env python3
"""测试try-except中的字符串异常"""

def check_datetime(s):
    """检查时间格式"""
    if len(s) == 8:
        try:
            raise '您输入的时间不正确'()
        except BaseException:
            print('error')
