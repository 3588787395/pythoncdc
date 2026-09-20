# -*- coding: utf-8 -*-
"""R14-15 负对照：两个推导式分别走 **STORE_SUBSCR**（逐键赋值），不坍缩。

形状：
  d = {}; d['a'] = [x for x in t]; d['b'] = [y for y in u]; return d
每条 STORE_SUBSCR 语句把上一个推导式的值**消费并终止**在该块内，
两个 MAKE_FUNCTION 之间存在语句终止符（STORE_*），
探测器取到的 `_first_call_end` 之后先碰到 STORE_SUBSCR ⇒ 不焊接，
表达式由通用路径重建（`_split_subscr_operands` / STORE_SUBSCR 分支）。
这条对照与 r14_10（关键字实参：同族 dict 语义但**会**坍缩）一起说明：
问题不在 dict 语义，而在「两条推导式之间没有任何语句终止符」时的配对判据。
期望：MATCH（负对照，必须保持一致）。
"""


def store_subscr_two_comps(t, u):
    d = {}
    d['a'] = [x for x in t]
    d['b'] = [y for y in u]
    return d


def two_statements_two_comps(t, u):
    a = [x for x in t]
    b = [y for y in u]
    return a, b
