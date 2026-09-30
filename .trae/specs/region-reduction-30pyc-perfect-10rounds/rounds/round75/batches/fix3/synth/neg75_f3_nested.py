# -*- coding: utf-8 -*-
# [R75 fix3 synth] 负例：真嵌套 try（两层 handler），两臂必须逐字节相同
def neg_nested_try(x):
    try:
        try:
            return 10 / x
        except ZeroDivisionError:
            return -1
    except Exception:
        return -2


def neg_nested_try_loop(n):
    total = 0
    try:
        try:
            for i in range(n):
                total += i
        except ValueError:
            total = 0
        return total
    except RuntimeError:
        return -3
