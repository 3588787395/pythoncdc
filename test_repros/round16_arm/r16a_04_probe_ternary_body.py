# -*- coding: utf-8 -*-
"""R16-A 04 探针：try 体唯一语句是**三元表达式**（TernaryRegion 而非 BoolOpRegion）。

预生成循环 `for child in region.children`（region_ast_generator.py:13947）同时接受
BoolOpRegion 与 TernaryRegion，所以理论上三元也应能抢走 try 的入口块。
本项检验「是否两类值区域都能触发」，以及症状是否与 02 完全一致。

若 MATCH ⇒ 只有 BoolOp 走到标记（三元另有出口），须据此收窄候选谓词。
"""


def check_ternary_body(value):
    if isinstance(value, str):
        try:
            valid = 'big' if int(value) > 100 else 'small'
        except ValueError:
            valid = None
        return valid
    return None
