"""
Defect 08 (R1 残留，已演化) — TERNARY/IF：嵌套 IfExp 作 if 条件时丢失 + 循环体裸 Name / 重复语句
================================================================
关联 R1 repro：repro_08_ternary_in_if_condition（R1：if 条件变 `len(...)` 裸 Expr）。

R2 复现状态：**复现（形态演化）**。
  R1 表现：`if (ternary):` 条件变 `len(ternary)` 裸 Expr
  R2 表现（quotation.pyc::load_get_price line 497-510）：
    —— 原 `if fq == 'pre':` 分支内 `for stock in panel.items: data = change_his_to_forward(...)`
       的赋值目标 `data` 丢失，循环体退化为裸 `stock` Expr；且 `elif fq == 'post':` 分支
       出现重复 `exrights_data = get_exrights_data(...)` 与裸 `panel.items` Expr；
       原嵌套 IfExp 的 if 条件整体仍丢失。
    R2 line 501 `stock`（裸 Name）、line 504 `panel.items`（裸 Expr）、
    line 505 重复 `exrights_data = get_exrights_data(...)`、line 508 `stock`（裸 Name）。

触发区域类型：TERNARY (IfExp) + LOOP (for + 赋值目标丢失) + 重复语句
根因初判：
    `core/cfg/region_ast_generator.py::_generate_if` / `_generate_loop` 在归约
    `for x in it: var = call(x, ...)` 时，把 `STORE_FAST var` 的赋值目标丢失，
    只保留迭代变量 `x` 作为裸 Expr；同时 `_build_effective_stmts` 对
    `exrights_data = get_exrights_data(...)` 这类前驱语句重复发射。
    违反「每块唯一归属」+「入口引用语义」。

最小字节码模式（Python 3.11，for + STORE_FAST 目标 + 前驱赋值）：
    <if fq == 'pre'>:
      LOAD_GLOBAL get_exrights_data / LOAD_FAST stocks / CALL   # exrights_data = ...
      STORE_FAST exrights_data
      LOAD_FAST panel / LOAD_ATTR items / GET_ITER
    FOR_ITER to <end>
      STORE_FAST stock
      LOAD_GLOBAL change_his_to_forward / LOAD_FAST stock / ... / CALL
      STORE_FAST data                       # ← data 目标丢失 → 裸 stock
      JUMP_BACKWARD

R2 反编译产物（错误）：
    if fq == 'pre':
        exrights_data = get_exrights_data(stocks, start)
        for stock in panel.items:
            data = change_his_to_forward(stock, panel[stock], exrights_data, start, end, typet)
            stock                          # ← 裸 Name
    elif fq == 'post':
        exrights_data = get_exrights_data(stocks, start)
        panel.items                        # ← 裸 Expr
        exrights_data = get_exrights_data(stocks, start)   # ← 重复
        for stock in panel.items:
            data = change_his_to_backward(...)
            stock                          # ← 裸 Name
期望产物：
    if fq == 'pre':
        exrights_data = get_exrights_data(stocks, start)
        for stock in panel.items:
            data = change_his_to_forward(stock, panel[stock], exrights_data, start, end, typet)

验证：python pycdc.py <this>.pyc  # 观察循环体裸 Name + 重复语句
"""
def load_get_price(stocks, typet, start, end, count, fq=None):
    panel = load_bars_from_hundsun(stocks, typet, start, end)
    if fq == 'pre':
        exrights_data = get_exrights_data(stocks, start)
        for stock in panel.items:
            data = change_his_to_forward(stock, panel[stock], exrights_data, start, end, typet)
    elif fq == 'post':
        exrights_data = get_exrights_data(stocks, start)
        for stock in panel.items:
            data = change_his_to_backward(stock, panel[stock], exrights_data, start, end, typet)
    return panel
