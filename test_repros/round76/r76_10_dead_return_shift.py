# -*- coding: utf-8 -*-
# R76-F 复现（对照 Quote.check_frequency，round3 r3_11 同型）：
# try 体 = 全终结 if/elif/else raise 链 + 链后不可达 `return None`。
# 预期缺陷：不可达 return 被 JUMP_FORWARD 替换并复制到函数尾。
def f(frequency):
    try:
        if frequency in ('1m', '5m', '15m'):
            raise ValueError('minute freq')
        elif frequency in ('30m', '60m'):
            raise ValueError('hour freq')
        else:
            assert frequency in ('1d', '1w'), 'bad freq'
        return None
    except Exception as e:
        log(str(e))
        return None
