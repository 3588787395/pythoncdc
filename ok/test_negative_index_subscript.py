"""测试负数下标问题"""

def func(tmp):
    # 原始代码可能是：open_am = tmp['open_am'] + -2[None] + ':00'
    # 这看起来像是反编译器错误地处理了某些表达式
    open_am = tmp['open_am'] + -2 + ':00'
    return open_am
