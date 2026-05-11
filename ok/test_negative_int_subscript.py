"""测试负数整数下标问题"""

def func(tmp):
    # 原始代码可能是：open_am = tmp['open_am'] + -2 + ':00'
    # 但反编译器错误地生成了：open_am = tmp['open_am'] + -2[None] + ':00'
    open_am = tmp['open_am'] + -2 + ':00'
    return open_am
