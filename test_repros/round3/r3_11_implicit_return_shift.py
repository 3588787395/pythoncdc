"""R3-B: try 体以全终结（raise/assert）if/elif/else 链结尾 —— 不可达隐式 return None 的
位置被重排（JUMP_FORWARD 代替 + 函数尾复制两份 return None）。
对照 quote.pyc check_frequency: orig O99-100 `LOAD_CONST None; RETURN_VALUE` 位于
RAISE_VARARGS 与 PUSH_EXC_INFO 之间; 反编译输出改为 JUMP_FORWARD 且函数尾出现双份 return None。"""


def check_frequency(self, frequency):
    try:
        if frequency.endswith('d') or frequency.endswith('m'):
            if frequency[:-1].isdigit():
                pass
            else:
                raise ValueError("您输入的频率有误, 请使用'Xd'/'Xm'的形式")
            assert int(frequency[:-1]) > 0, "您输入的频率有误, 'X'需要是一个正整数"
        elif frequency in ('w', 'mo'):
            assert int(frequency[:-1]) > 0, "您输入的频率有误, 'X'需要是一个正整数"
        else:
            raise ValueError("您输入的频率有误, 请使用'daily'或'minute'")
    except BaseException:
        self.trade_log.error("您输入的频率有误，使用'Xd'/'Xm'的形式")
        raise
    return self.check_frequency_end(frequency)


def check_frequency_end(self, frequency):
    return frequency
