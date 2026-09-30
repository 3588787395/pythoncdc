# -*- coding: utf-8 -*-
# 负对照：`if x:` 臂含终结核 try/except + elif 链，但臂无前导赋值
# （try 是臂首语句 → 编译器内联，不触发冷布局差异）。
def f(redata, flag):
    if redata:
        try:
            if redata:
                return work(redata)
            log('empty')
            return None
        except BaseException as x:
            log('err: ' + str(x))
            return None
    elif flag == 1:
        log('conv error')
    elif flag == -1:
        log('empty resp')
    return None
