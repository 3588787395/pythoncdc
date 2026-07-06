"""测试复杂字符串切片表达式"""

def func(tmp):
    # 原始代码: open_am = tmp['open_am'][:2] + ':' + tmp['open_am'][-2:] + ':00'
    # 这是一个复杂的字符串拼接表达式
    open_am = tmp['open_am'][:2] + ':' + tmp['open_am'][-2:] + ':00'
    return open_am
