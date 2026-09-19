# Source Generated with Decompyle++ (Python version)
# File: r3_03_while_retry_loop.pyc (Python 3.11)

__doc__ = """R3-L: while not A and B: 重试循环 —— 条件 and→or 反演 + 循环体丢失。
对照 quote.pyc check_limit / initImagedata / get_real_from_zeromq 的 zeromq 重试循环:
    while not redata and count < 3:
        time.sleep(n); if flag == 1: ... elif flag == -1: ...
        redata, flag = self.api(str(params)); count += 1
无 f-string, 纯净隔离该模式。"""
def retry_fetch(self, universe):
    params = ['snapshot']
    if isinstance(universe, str):
        params.append(universe)
    else:
        return {}
    redata, flag = self.api(str(params))
    count = 0
    while not redata and count < 3:
        self.sleep(3)
        if flag == 1:
            self.warn('获取数据异常，重试')
        elif flag == -1:
            self.warn('获取数据为空，重试')
        redata, flag = self.api(str(params))
        count += 1
    result = {}
    for code in universe:
        result[code] = 1
    return result
