# -*- coding: utf-8 -*-
# synth a01 -- F-ABSORB ① "and 链共享 else" 最小复现（形态取自
# IQCommon/data/finance.pyc::get_financial_and_growth_factors 头部）。
# 期望：landed（R72 HEAD）反编译成「两层嵌套 if + 内层 else 吞掉共享 else」
# （外层 start_year 无 else），首条分歧落在 POP_JUMP_FORWARD_IF_NOT_NONE 落点；
# abs1（same-target 豁免）反编译成扁平 `if A and B: ... else: ...`，与 pyc 逐位一致。
def synth_a01_shared_and_else(date, start_year, end_year, now):
    if not date:
        if start_year is None and end_year is None:
            date = get_qry_date(now, date=date)
            date = int(date)
        else:
            date = None
    return date


def get_qry_date(now, date=None):
    return now if date is None else date


def synth_a01_caller(date, start_year, end_year):
    return synth_a01_shared_and_else(date, start_year, end_year, 20240101)
