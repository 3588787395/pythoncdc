# -*- coding: utf-8 -*-
# Round 30 CONTROL battery for R30-C1 —— 判据邻位的四个结构形状，必须逐字节不动。
# MEASURED: landed core 与 R30-C1 两侧均 matched 6/6、mism=[]，且两份产物 **sha 逐字节相同**
# （ef52a76276145780）⇒ 该判据可证不触及：(a) 内层 loop 自己的回边（终止指令跳向**本**头部）、
# (b) 真 break（终止指令是向前跳转）、(c) for 套 for 的 break、(d) while True 破出且区域出口块
# 之后无块。注意：本文件里的 `witness` 函数是那 6 个匹配函数之一，它是 CONTROL 不是见证 ——
# 会失败的中心形状在 r30c_w2.pyc。

"""Round 30 line-C synthetic witness + controls, compiled with the shipping interpreter.

Witness (R30-C shape): the *outer* for-loop's back-edge block is simultaneously reachable as
the *inner* while-loop's break exit.  Its terminal instruction is a backward jump to the
ENCLOSING loop's header, so it is not a break of the inner region at all -- but the analyzer
verifies it as one, it enters the inner region's block set, and the inner loop's render then
marks it generated.  Nobody emits it.

Controls are shapes that must be byte-identical under the candidate:
  control_continue_target_self  -- inner loop's own back edge (terminal jumps to THIS header)
  control_break_forward         -- a real break: terminal is a forward jump past the loop
  control_nested_for_break      -- break in a for nested in a for (both exits forward)
  control_while_true_break      -- while True with a break (no region exit block follows)
"""


def witness(dates, queue, log):
    for day in dates:
        n = 0
        while queue:
            n += queue.pop()
            if n > 10:
                break
        log(day, n)
    return len(dates)


def control_continue_target_self(dates, queue, log):
    for day in dates:
        while queue:
            item = queue.pop()
            if item is None:
                continue
            log(item)
    return len(dates)


def control_break_forward(dates, queue, log):
    for day in dates:
        while queue:
            if len(queue) > 3:
                break
            log(queue.pop())
    return len(dates)


def control_nested_for_break(dates, others, log):
    for day in dates:
        for other in others:
            if other == day:
                break
            log(other)
    return len(dates)


def control_while_true_break(dates, log):
    for day in dates:
        while True:
            log(day)
            break
    return len(dates)
