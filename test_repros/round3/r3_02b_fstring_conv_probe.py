"""R3-A 触发条件探针: 同一 f-string 日志语句, 区分带 !s 转换与不带 !s 的操作数。
工作对照: f'...{a!s}...{b!s}...' (run_individual_transform 中存活)
坏例对照: f'...{x[None:10]!s}...{len(x)}...' (check_limit/initImagedata 中被丢) """


class Q3:
    def __init__(self):
        self.log = L3()


class L3:
    def __init__(self):
        self.quote = QT()


class QT:
    def debug(self, msg):
        pass


def probe_bang_s(self, universe):
    self.log.quote.debug(f'开始第{self.n!s}次订阅，包括{universe[:10]!s}等{len(universe)!s}只代码')
    total = 0
    for item in universe:
        total += len(item)
    return total


def probe_plain(self, universe):
    self.log.quote.debug(f'开始第{self.n!s}次订阅，包括{universe[:10]!s}等{len(universe)}只代码')
    total = 0
    for item in universe:
        total += len(item)
    return total
