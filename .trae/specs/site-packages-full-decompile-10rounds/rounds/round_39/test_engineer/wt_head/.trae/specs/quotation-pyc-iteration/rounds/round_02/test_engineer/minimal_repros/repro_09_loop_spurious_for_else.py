"""
Defect 09 (R1 残留) — LOOP: spurious for-else（双层 for + match case 体内均误生成 for-else）
================================================================
关联 R1 repro：repro_09_loop_spurious_for_else（R1：双层 spurious for-else）。

R2 复现状态：**复现**。
  quotation.pyc::fill_missing_stock_data line 2120-2129（R2 产物）：
        for stock in secu_filled_list:
            for date in end_date_return:
                data_tmp = dict()
                data_list.append(data_tmp)
            else:
                continue                   # ← 内层 spurious else
        else:
            data_filled = pandas.DataFrame(data_list, columns=data.columns)   # ← 外层 spurious else
            data = data.append(data_filled)
            return data
  另：quotation.pyc::get_str_data line 1960-1968 match case 体内的 for 也被加上
  spurious `else: continue`。

触发区域类型：LOOP (for 循环 + for-else 误生成)
根因初判：
    `core/cfg/region_analyzer.py::_identify_loop_regions` 的 else 归属判定：
    CPython 对 `for x in it: body`（无 else）编译为
    `FOR_ITER ... JUMP_BACKWARD; <fall-through>: <next stmts>`，
    fall-through 块同时是循环出口与后续语句入口。归约器把 fall-through 中的
    后续语句错误识别为 for-else 的 body，且对嵌套 for / match case 内的 for
    也重复该错误（内层 for 被加上 `else: continue`）。
    违反「每块唯一归属」：fall-through 应归循环出口 + 后续顺序语句。

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

R2 反编译产物（错误，双层 spurious for-else）：
    for stock in secu_filled_list:
        for date in end_date_return:
            data_tmp = dict()
            data_list.append(data_tmp)
        else:
            continue
    else:
        data_filled = pandas.DataFrame(data_list, columns=data.columns)
        data = data.append(data_filled)
        return data
期望产物：
    for stock in secu_filled_list:
        for date in end_date_return:
            data_tmp = dict()
            data_list.append(data_tmp)
    data_filled = pandas.DataFrame(data_list, columns=data.columns)
    data = data.append(data_filled)
    return data

验证：python pycdc.py <this>.pyc  # 观察双层 spurious for-else
"""
def fill_missing_stock_data(security, data):
    secu_code_return = data['secu_code'].unique()
    end_date_return = data['end_date'].unique()
    secu_filled_list = list(set(security) - set(secu_code_return))
    data_list = list()
    for stock in secu_filled_list:
        for date in end_date_return:
            data_tmp = dict()
            data_list.append(data_tmp)
    data_filled = pandas.DataFrame(data_list, columns=data.columns)
    data = data.append(data_filled)
    return data
