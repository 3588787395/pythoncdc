"""
Defect R3-11 (R1/R2 残留) — IF/ELIF：elif 分支首条赋值 RHS 丢失→裸 Name + 重复赋值
================================================================
关联 R1/R2 repro：repro_11_if_elif_dup_and_bare_expr / repro_11_if_elif_bare_name

R3 复现状态：**R2 未修复，quotation.pyc::check_stocks (line 1910-1915)、dict_to_dataframe (line 1939)
            仍复现**。
  R3 表现（quotation.pyc::check_stocks）：
        elif isinstance(l, list) or isinstance(l, tuple):
            l                                # ← 裸 Name（原 l = l.replace('.XSHE', '.SZ') 的 RHS 丢失）
            for s in l:
                s = s.replace('.XSHE', '.SZ')
                check_stock(s)

触发区域类型：IF/ELIF（isinstance 链）+ 赋值 RHS 丢失
根因初判：
    `region_ast_generator.py::_generate_if` 在 elif 分支内重建 `l = l.replace(...)` 时，
    把 `LOAD_FAST l + LOAD_ATTR replace + CALL_METHOD` 的 Call 节点丢弃，
    只保留 receiver `LOAD_FAST l` 作孤立 Expr，并对前驱赋值重复发射。
    违反「每块唯一归属」。

最小字节码模式（Python 3.11）：
    LOAD_GLOBAL isinstance
    LOAD_FAST l
    LOAD_GLOBAL list
    CALL
    POP_JUMP_IF_FALSE
    LOAD_GLOBAL isinstance              # ← or 短路第二支
    LOAD_FAST l
    LOAD_GLOBAL tuple
    CALL
    POP_JUMP_IF_TRUE                    # ← elif isinstance(l, list) or isinstance(l, tuple):
    LOAD_FAST l                         # ← l = l.replace(...)  ← RHS Call 丢失，只剩 receiver
    POP_TOP                             # ← 裸 l Expr
    LOAD_FAST l                         # ← 重复赋值（前驱语句重复发射）
    LOAD_ATTR replace
    LOAD_CONST '.XSHE'
    LOAD_CONST '.SZ'
    CALL_METHOD
    STORE_FAST l

R3 反编译产物（错误）：
    elif isinstance(l, list) or isinstance(l, tuple):
        l                                # ← 裸 Name
        l = l.replace('.XSHE', '.SZ')    # ← 重复赋值（最小复现中保留）
        for s in l:
            s = s.replace('.XSHE', '.SZ')
            s = s.replace('.XSHG', '.SS')
            check_stock(s)

期望产物：
    elif isinstance(l, list) or isinstance(l, tuple):
        l = l.replace('.XSHE', '.SZ')
        for s in l:
            s = s.replace('.XSHE', '.SZ')
            s = s.replace('.XSHG', '.SS')
            check_stock(s)

验证：
    $ python3 -c "import py_compile; py_compile.compile('repro_03_if_elif_bare_name.py', 'repro_03_if_elif_bare_name.pyc', doraise=True)"
    $ python pycdc.py repro_03_if_elif_bare_name.pyc
    # 观察 elif 分支出现裸 l Expr 与重复 l = l.replace(...) 赋值
"""
def check_stocks(l):
    if isinstance(l, str):
        l = l.replace('.XSHE', '.SZ')
        l = l.replace('.XSHG', '.SS')
        check_stock(l)
    elif isinstance(l, list) or isinstance(l, tuple):
        l = l.replace('.XSHE', '.SZ')
        for s in l:
            s = s.replace('.XSHE', '.SZ')
            s = s.replace('.XSHG', '.SS')
            check_stock(s)
    else:
        raise RuntimeError('您的输入有误')
