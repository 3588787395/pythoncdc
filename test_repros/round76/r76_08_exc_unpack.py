# -*- coding: utf-8 -*-
# R76-D3 复现（对照 Quote.get_real_from_zeromq 的 handler）：
# except 内 `exc_type, exc_obj, exc_tb = sys.exc_info()` + 对 exc_tb 的引用。
# 预期缺陷：元组解包降级为单赋值，exc_obj/exc_tb 变全局引用。
import sys
import os

def f():
    try:
        return work()
    except BaseException as x:
        log('error here: ' + str(x))
        print('print here')
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print('exc info:', exc_type, fname, exc_tb.tb_lineno)
        log('real data error: ' + str(x))
        return None
