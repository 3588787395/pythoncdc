"""
Defect R3-09 (R1/R2 残留) — LOOP：双层 spurious for-else（含循环后语句误归 else body）
================================================================
关联 R1/R2 repro：repro_09_loop_spurious_for_else

R3 复现状态：**R2 未修复，quotation.pyc::fill_missing_stock_data (line 2117-2126)、get_str_data
            (line 536-556) 仍复现，含双层 for + while-else 新形态**。
  R3 表现（quotation.pyc::fill_missing_stock_data）：
        for stock in secu_filled_list:
            for date in end_date_return:
                data_tmp = dict()
                data_list.append(data_tmp)
            else:
                continue                   # ← 内层 spurious else
        else:
            data_filled = pandas.DataFrame(...)   # ← 外层 spurious else
            data = data.append(data_filled)
            return data

触发区域类型：LOOP（for 循环 + for-else 误生成，双层 + 嵌套）
根因初判：
    `region_ast_generator.py::_identify_loop_regions` 的 else 归属判定把 fall-through 后续语句
    误识别为 for-else body，对嵌套 for / while 重复该错误。
    违反「每块唯一归属」：循环后顺序语句应作为函数体子节点，不应归 for-else。

最小字节码模式（Python 3.11）：
    GET_ITER
    FOR_ITER to <outer_end>
      STORE_FAST stock
      GET_ITER
      FOR_ITER to <inner_end>
        STORE_FAST date
        BUILD_MAP
        STORE_FAST data_tmp
        LOAD_FAST data_list
        LOAD_METHOD append
        LOAD_FAST data_tmp
        CALL
        POP_TOP
      JUMP_BACKWARD to <inner_start>      # ← 内层无 break，不应有 else
    JUMP_BACKWARD to <outer_start>        # ← 外层无 break，不应有 else
    <outer_end>:
      LOAD_GLOBAL pandas
      ...
      STORE_FAST data_filled              # ← 循环后语句，被误归 else body

R3 反编译产物（错误）：
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

验证：
    $ python3 -c "import py_compile; py_compile.compile('repro_03_loop_spurious_for_else_double.py', 'repro_03_loop_spurious_for_else_double.pyc', doraise=True)"
    $ python pycdc.py repro_03_loop_spurious_for_else_double.pyc
    # 观察双层 for 均出现 spurious else，循环后语句被误归外层 else body
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
