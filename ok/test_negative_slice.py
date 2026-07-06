"""测试负数切片问题"""

def func(tmp):
    # 原始代码: open_am = tmp['open_am'][:-2] + ':00'
    # 但反编译器错误地生成: open_am = tmp['open_am'] + -2[None] + ':00'
    open_am = tmp['open_am'][:-2] + ':00'
    return open_am
