"""测试从末尾切片的语法"""

def func():
    # 原始代码: out_trade_times = trade_times[1:-1]
    # 但反编译器可能错误地生成: out_trade_times = trade_times[1[-1]]
    trade_times = [1, 2, 3, 4, 5]
    out_trade_times = trade_times[1:-1]
    return out_trade_times
