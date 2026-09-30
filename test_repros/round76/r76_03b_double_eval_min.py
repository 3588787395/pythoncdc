# -*- coding: utf-8 -*-
# R76-A2 变体（最小化）：两语句前导 + `if A and B:` 体含 if + for。
def f(a, b, c):
    x = first(a)
    y = second(b)
    if check(x) and b == 6:
        if isinstance(c, str):
            c = [c]
        for i in c:
            work(i)
    return y
