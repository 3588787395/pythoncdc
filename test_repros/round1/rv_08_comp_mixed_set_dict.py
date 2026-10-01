# rv_08 修复二 comprehension 甄别窗 嵌套变体 2：
# setcomp / dictcomp 过滤器混合链（推导式其他类别），推导式再嵌 while 内


def f(vals, a, b, c):
    n = 0
    out_s = None
    out_d = None
    while n < 2:
        s = {v for v in vals if a and b or c}
        d = {v: n for v in vals if a and b or c}
        out_s = s
        out_d = d
        n += 1
    return out_s, out_d
