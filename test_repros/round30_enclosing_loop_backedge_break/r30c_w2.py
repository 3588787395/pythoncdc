# -*- coding: utf-8 -*-
# Round 30 G0 WITNESS battery for candidate R30-C1 —— 内层 loop 的 break 角色核验抢走
# 「承载外层 loop 回边」的那一块（原则 2 每块唯一归属的 break-role 侧；只删不增）。
# MEASURED on both cores (mirror root D:/Temp/r30gate/c1, `python -X utf8 r30c.py run`):
#   landed core   r30c_w2.pyc  matched 3/6
#     mism = [['w_a_true_break_epilogue', 27, 21, 1, 11],
#             ['w_b_true_break_yield_epilogue', 23, 19, 0, 23],
#             ['w_e_deep', 30, 26, 0, 30]]
#   + R30-C1      r30c_w2.pyc  matched 6/6, mism=[]
#                  产物 sha d17b0ae28839af5e -> 82e204835d56eeed
# 三个缺陷函数的共同形状：外层 for 的循环体在**嵌套 while 之后**还有语句，承载那些尾语句的
# 块以「向后跳到 for 头部」结尾 —— 该终止指令是外层 loop 的回边，不是内层 loop 的 break 出口，
# 但内层的 break 核验仍把它收进区域块集，内层渲染的批量入账随即令它无人发射。
# w_c_for_break_yield / w_d_try_inside 原以为是同族见证，实测两核均 6/6 干净：
# 「嵌套 loop 之后的任意块」这条拇指规则太弱，起作用的是**向后跳转终止指令**本身。
# 记为负结果，不算通过的见证。

"""Round 30 line-C witness CANDIDATE battery (probe which structural extra ingredient makes the
parent loop's back-edge block get verified as a break block of the nested loop)."""


def w_a_true_break_epilogue(dates, queue, log):
    # for -> while True: -> break ; epilogue with a call, then loop back edge
    for day in dates:
        while True:
            if not queue:
                break
            log(queue.pop())
        log('done', day)
    return len(dates)


def w_b_true_break_yield_epilogue(dates, queue, log):
    # generator: the for-loop's back-edge block ends in a yield statement
    for day in dates:
        while True:
            if not queue:
                break
            log(queue.pop())
        yield day


def w_c_for_break_yield(dates, queue, log):
    # nested FOR (not while) inside the outer for, epilogue yield
    for day in dates:
        for item in queue:
            log(item)
        yield day


def w_d_try_inside(dates, queue, log):
    for day in dates:
        try:
            while queue:
                if log():
                    break
        except ValueError:
            log('x')
        yield day


def w_e_deep(dates, queue, log):
    for day in dates:
        while True:
            if not queue:
                break
            for item in queue:
                if item:
                    break
            log(item)
        yield day
