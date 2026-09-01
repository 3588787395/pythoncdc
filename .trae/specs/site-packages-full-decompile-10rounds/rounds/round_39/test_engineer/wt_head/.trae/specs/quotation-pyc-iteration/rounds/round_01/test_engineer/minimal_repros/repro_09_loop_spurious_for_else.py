"""
Defect 09 — LOOP: spurious for-else (循环后代码被错误归入 for-else 块)
================================================================
触发区域类型：LOOP (for 循环 + for-else 误生成)
根因初判：
    core/cfg/region_analyzer.py `_identify_loop_regions` 的 else
    归属判定：CPython 对 `for x in it: body` (无 else) 编译为
    `FOR_ITER ... JUMP_BACKWARD; <fall-through>: <next stmts>`，
    fall-through 块同时是循环出口与后续语句的入口。归约器把
    fall-through 中的后续语句（如 `data_filled = ...; data = ...;
    return data`）错误识别为 for-else 的 body，且对嵌套 for 也
    重复该错误（内层 for 也被加上 `else: continue`）。
    违反「每块唯一归属」：fall-through 块应归为循环出口 + 后续
    顺序语句，不应整体划给 for-else。

最小字节码模式（Python 3.11，for 无 else）：
    FOR_ITER to <end>
      STORE_FAST stock
      FOR_ITER to <inner-end>          # 内层 for
        STORE_FAST date
        <inner body>
        JUMP_BACKWARD to <inner-for>
      <inner-end>:                     # 内层 fall-through
      JUMP_BACKWARD to <outer-for>
    <end>:                             # 外层 fall-through
      <后续语句: data_filled = ...; return data>

反编译产物（错误，双层 spurious for-else）：
    for stock in secu_filled_list:
        for date in data['end_date'].unique():
            data_tmp = dict()
            data_list.append(data_tmp)
        else:
            continue                   # ← 内层 spurious else
    else:
        data_filled = pandas.DataFrame(data_list, columns=data.columns)   # ← 外层 spurious else
        data = data.append(data_filled)
        return data
期望产物：
    for stock in secu_filled_list:
        for date in data['end_date'].unique():
            data_tmp = dict()
            data_list.append(data_tmp)
    data_filled = pandas.DataFrame(data_list, columns=data.columns)
    data = data.append(data_filled)
    return data

验证：python pycdc.py <this>.pyc
"""
def fill_missing_stock_data(security, data):
    secu_code_return = data['secu_code'].unique()
    secu_filled_list = list(set(security) - set(secu_code_return))
    data_list = list()
    for stock in secu_filled_list:
        for date in data['end_date'].unique():
            data_tmp = dict()
            data_list.append(data_tmp)
    data_filled = pandas.DataFrame(data_list, columns=data.columns)
    data = data.append(data_filled)
    return data
