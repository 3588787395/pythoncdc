"""R3-A(b): f-string 日志语句（{x[None:10]!s} 切片 + {len(x)} 调用操作数）整体丢失。
对照 quote.pyc check_limit / initImagedata / get_real_from_zeromq 中部日志语句。"""


def check_limit(self, universe):
    tmp_universe = universe
    params = ['snapshot']
    if isinstance(universe, str):
        params.append(universe)
        tmp_universe = [universe]
    elif isinstance(universe, (list, tuple)):
        for item in universe:
            params.append(item)
    else:
        return {}
    redata, flag = self.api(str(params))
    count = 0
    while not redata and count < 3:
        time_sleep(3)
        if flag == 1:
            self.log_quote_warn('获取snapshot数据异常，重试')
        elif flag == -1:
            self.log_quote_warn('获取snapshot返回为空，重试')
        redata, flag = self.api(str(params))
        count += 1
    self.log_quote_info(f'在线获取snapshot数据判断涨跌停,包括{tmp_universe[None:10]!s}等{len(tmp_universe)}只代码')
    result = {}
    for code in tmp_universe:
        result[code] = 1
    return result


def time_sleep(n):
    pass
