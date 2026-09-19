"""R3-A(a): f-string 日志语句（含 {x[None:10]!s} 切片 + 条件表达式操作数）模板错乱 + 调用接收者丢失。
对照 quote.pyc get_price / load_bars_from_hundsun / load_get_price 首条日志语句。"""


class Q:
    def __init__(self):
        self.log = Log()


class Log:
    def __init__(self):
        self.quote = Quoter()


class Quoter:
    def debug(self, *a):
        pass


def get_price(self, security, start_date='20150101', end_date='20151231', frequency='daily'):
    self.log.quote.debug(f'调用函数get_price，参数为：stocks={security[None:10]!s}等{len(security) if isinstance(security, list) else 1}只代码,frequency={frequency},start_date={start_date},end_date={end_date}')
    data = {}
    if isinstance(security, str):
        security = [security]
    for s in security:
        data[s] = [1, 2, 3]
    if len(data) > 0:
        for k in list(data.keys()):
            data[k] = data[k] + [4]
    return data
