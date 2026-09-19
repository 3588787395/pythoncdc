# Source Generated with Decompyle++ (Python version)
# File: r3_01_fstring_log_mangled.pyc (Python 3.11)

__doc__ = """R3-A(a): f-string 日志语句（含 {x[None:10]!s} 切片 + 条件表达式操作数）模板错乱 + 调用接收者丢失。
对照 quote.pyc get_price / load_bars_from_hundsun / load_get_price 首条日志语句。"""
class Q:
    def __init__(self):
        self.log = Log()
class Log:
    def __init__(self):
        self.quote = Quoter()
class Quoter:
    def debug(self, *a):
        return None
def get_price(self, security, start_date='20150101', end_date='20151231', frequency='daily'):
    if self.log.quote.debug(len(security) if isinstance(security, list) else 1):
        pass
    for s in security:
        data[s] = [1, 2, 3]
    if len(data) > 0:
        for k in list(data.keys()):
            data[k] = data[k] + [4]
    return data
