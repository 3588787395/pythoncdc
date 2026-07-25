"""
Defect 16 (R2 新增) — COMPARE/CONTAINS_OP：`x not in S` 被误重建为 `x in S`
================================================================
R1 关联：repro_02（同源：IS_OP / CONTAINS_OP 反向跳转误读）。

R2 复现状态：**新出现**。
  quotation.pyc::get_history line 779（R2 产物）：
        elif frequency in OVER_WEEK_FREQUENCY and query_date == None:
  —— 原 `elif frequency not in OVER_WEEK_FREQUENCY and query_date is None:`
     中 `not in`（CONTAINS_OP 0 + POP_JUMP_FORWARD_IF_FALSE）被误重建为 `in`。
     与 repro_02 的 `is None → == None` 同源：反向跳转条件块归属错位。

触发区域类型：COMPARE (CONTAINS_OP, not in → in)
根因初判：
    `core/cfg/region_ast_generator.py::_generate_compare` 把
    `CONTAINS_OP 0`（not in）+ `POP_JUMP_FORWARD_IF_FALSE` 的组合误读为
    正向 `in`，丢失 `not`。`CONTAINS_OP` 的 arg（0=not in, 1=in）未被正确解析。
    违反「每块唯一归属」：CONTAINS_OP 的反向位应归 not-in 条件块。

最小字节码模式（Python 3.11，x not in S）：
    LOAD_GLOBAL frequency
    LOAD_GLOBAL OVER_WEEK_FREQUENCY
    CONTAINS_OP 0                          # 0 = not in
    POP_JUMP_FORWARD_IF_FALSE to <else>

R2 反编译产物（错误，not in → in）：
    elif frequency in OVER_WEEK_FREQUENCY and query_date == None:
        ...
期望产物：
    elif frequency not in OVER_WEEK_FREQUENCY and query_date is None:
        ...

验证：python pycdc.py <this>.pyc  # 观察 not in → in
"""
def get_history(frequency, query_date=None):
    if frequency not in OVER_WEEK_FREQUENCY and query_date is None:
        query_date = datetime.now()
    else:
        query_date = datetime.strptime(query_date, '%Y%m%d')
    return query_date
