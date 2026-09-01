"""
Defect R3-08 (R1/R2 残留) — TERNARY/LOOP：循环体裸 Name + 重复语句
================================================================
关联 R1/R2 repro：repro_08_ternary_in_if_condition / repro_08_ternary_condition_lost

R3 复现状态：**R2 未修复，quotation.pyc::load_get_price (line 497-510)、get_str_data、load_bars_from_hundsun
            等多处仍复现**。
  R3 表现（quotation.pyc::load_get_price）：
        if fq == 'pre':
            exrights_data = get_exrights_data(stocks, start)
            for stock in panel.items:
                data = change_his_to_forward(stock, panel[stock], exrights_data, start, end, typet)
                stock                          # ← 裸 Name（赋值目标 data 已恢复，但 stock 裸 Expr 残留）
        elif fq == 'post':
            exrights_data = get_exrights_data(stocks, start)
            panel.items                        # ← 裸 Expr
            exrights_data = get_exrights_data(stocks, start)   # ← 重复
            for stock in panel.items:
                data = change_his_to_backward(...)
                stock                          # ← 裸 Name

触发区域类型：TERNARY(IfExp) + LOOP(for + 赋值目标丢失) + 重复语句
根因初判：
    `_generate_if`/`_generate_loop` 在归约 `for x in it: var = call(x, ...)` 时，
    迭代变量 `x` 被作为孤立 Expr 重复发射（疑似 STORE_SUBSCR `panel[x] = data` 的下标/目标丢失）；
    `_build_effective_stmts` 对前驱赋值（exrights_data = ...）重复发射。
    违反「每块唯一归属」+「入口引用语义」。

最小字节码模式（Python 3.11）：
    LOAD_FAST fq
    LOAD_CONST 'pre'
    COMPARE_OP ==
    POP_JUMP_IF_FALSE
      LOAD_GLOBAL get_exrights_data
      ...
      CALL
      STORE_FAST exrights_data          # ← exrights_data = get_exrights_data(...)
      GET_ITER
      FOR_ITER
        STORE_FAST stock
        LOAD_GLOBAL change_his_to_forward
        LOAD_FAST stock
        ...
        CALL
        STORE_FAST data                 # ← data = change_his_to_forward(...)
        LOAD_FAST stock                 # ← 裸 stock Expr（疑似 panel[stock] = data 目标丢失）
        POP_TOP

R3 反编译产物（错误）：
    if fq == 'pre':
        exrights_data = get_exrights_data(stocks, start)
        for stock in panel.items:
            data = change_his_to_forward(stock, panel[stock], exrights_data, start, end, typet)
            stock                          # ← 裸 Name
    elif fq == 'post':
        exrights_data = get_exrights_data(stocks, start)
        panel.items                        # ← 裸 Expr
        exrights_data = get_exrights_data(stocks, start)   # ← 重复

期望产物：
    if fq == 'pre':
        exrights_data = get_exrights_data(stocks, start)
        for stock in panel.items:
            data = change_his_to_forward(stock, panel[stock], exrights_data, start, end, typet)
            if data is not None:
                panel[stock] = data

验证：
    $ python3 -c "import py_compile; py_compile.compile('repro_03_loop_bare_name_and_dup.py', 'repro_03_loop_bare_name_and_dup.pyc', doraise=True)"
    $ python pycdc.py repro_03_loop_bare_name_and_dup.pyc
    # 观察循环体出现裸 stock Expr 与重复 exrights_data 赋值
"""
def load_get_price(stocks, fq=None):
    panel = load_bars_from_hundsun(stocks)
    if fq == 'pre':
        exrights_data = get_exrights_data(stocks)
        for stock in panel.items:
            data = change_his_to_forward(stock, panel[stock], exrights_data)
            if data is not None:
                panel[stock] = data
    elif fq == 'post':
        exrights_data = get_exrights_data(stocks)
        for stock in panel.items:
            data = change_his_to_backward(stock, panel[stock], exrights_data)
            if data is not None:
                panel[stock] = data
    return panel
