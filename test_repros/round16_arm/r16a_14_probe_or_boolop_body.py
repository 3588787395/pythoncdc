# -*- coding: utf-8 -*-
"""R16-A 14 探针：try 体唯一语句是 `x = A or B`（BoolOp 换 or）。

`and` 的假分支用 JUMP_IF_FALSE_OR_POP（值留栈），`or` 用 JUMP_IF_TRUE_OR_POP，
BoolOpRegion 的 merge_block / blocks 形状略有不同。本项检验候选谓词是否对两种
布尔算子同效（谓词里只提「值上下文 BoolOpRegion」，不提算子）。
"""


def check_or_boolop_body(value):
    if isinstance(value, str):
        try:
            valid = int(value) < 0 or int(value) > 100
        except ValueError:
            valid = False
        return valid
    return False
