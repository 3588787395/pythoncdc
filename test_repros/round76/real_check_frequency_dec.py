# Source Generated with Decompyle++ (Python version)
# File: real_check_frequency.pyc (Python 3.11)

def check_frequency(self, frequency):
    if frequency in self.frequency_compat:
        frequency = self.frequency_compat.get(frequency)
    if not (frequency[-1:] == 'm' or frequency[-1:] == 'd' or frequency == 'w' or frequency == 'mo'):
        self.trade_log.error("您输入的频率有误, 请使用'Xd'/'Xm'的形式, 或'daily'(等价于'1d'), 或'minute'(等价于'1m'), 或'weekly'(等价于'w'), 或'monthly'(等价于'mo')")
    assert frequency[-1:] == 'm' or frequency[-1:] == 'd' or frequency == 'w' or frequency == 'mo', "您输入的频率有误, 请使用'Xd'/'Xm'的形式, 或'daily'(等价于'1d'), 或'minute'(等价于'1m'), 或'weekly'(等价于'w'), 或'monthly'(等价于'mo')"
    if frequency not in ('w', 'mo'):
        try:
            tmp = int(frequency[:-1])
        except BaseException:
            self.trade_log.error("您输入的频率有误, 使用'Xd'/'Xm'的形式, 'X'需要是一个正整数")
            assert False, "您输入的频率有误, 使用'Xd'/'Xm'的形式, 'X'需要是一个正整数"
        else:
            if not tmp > 0:
                self.trade_log.error("您输入的频率有误, 使用'Xd'/'Xm'的形式, 'X'需要是一个正整数")
            assert tmp > 0, "您输入的频率有误, 使用'Xd'/'Xm'的形式, 'X'需要是一个正整数"
        return None
