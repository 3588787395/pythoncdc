"""
Defect 11 (R1 残留，已演化) — IF/ELIF：elif 分支首条赋值语句退化为裸 Name Expr
================================================================
关联 R1 repro：repro_11_if_elif_dup_and_bare_expr（R1：裸 l + 重复赋值并存）。

R2 复现状态：**复现（形态演化）**。
  R1 表现：`l = l.replace(...)` + 裸 `l` + 重复 `l = l.replace(...)`（三者并存）
  R2 表现（quotation.pyc::check_stocks line 1909-1914）：
        elif isinstance(l, list) or isinstance(l, tuple):
            l                                # ← 裸 Name Expr（赋值 RHS 丢失）
            for s in l:
                s = s.replace('.XSHE', '.SZ')
                s = s.replace('.XSHG', '.SS')
                check_stock(s)
    —— R2 中重复赋值已消失（R1 重复问题部分解除），但 elif 分支首条
       `l = l.replace('.XSHE', '.SZ')` 的 RHS CALL 整体丢失，只剩裸 `l` Expr。

触发区域类型：IF/ELIF (isinstance 链) + 赋值 RHS 丢失
根因初判：
    `core/cfg/region_ast_generator.py::_generate_if` 在 elif 分支内重建
    `l = l.replace(...)` 时，把 `LOAD_FAST l + LOAD_ATTR replace + ... + CALL_METHOD`
    的 Call 节点丢弃，只保留 receiver `LOAD_FAST l` 作为孤立 Expr。
    违反「每块唯一归属」：LOAD_FAST l 应作为 Call 的 receiver 子节点。

最小字节码模式（Python 3.11，elif 分支首条 store + call_method）：
    LOAD_FAST l
    POP_JUMP_IF_FALSE ...               # isinstance check
    ...
    LOAD_FAST l                         # ← receiver 被误识别为 Expr(l)
    LOAD_ATTR replace
    LOAD_CONST '.XSHE'
    LOAD_CONST '.SZ'
    CALL_METHOD 2
    STORE_FAST l                        # l = l.replace(...)
    FOR_ITER ...                        # for s in l:

R2 反编译产物（错误，裸 l）：
    elif isinstance(l, list) or isinstance(l, tuple):
        l
        for s in l:
            s = s.replace('.XSHE', '.SZ')
            ...
期望产物：
    elif isinstance(l, list) or isinstance(l, tuple):
        l = l.replace('.XSHE', '.SZ')
        for s in l:
            s = s.replace('.XSHE', '.SZ')
            ...

验证：python pycdc.py <this>.pyc  # 观察 elif 首条赋值退化为裸 Name
"""
def check_stocks(l):
    if isinstance(l, str):
        l = l.replace('.XSHE', '.SZ')
        check_stock(l)
    elif isinstance(l, list) or isinstance(l, tuple):
        l = l.replace('.XSHE', '.SZ')
        for s in l:
            s = s.replace('.XSHE', '.SZ')
            check_stock(s)
    else:
        raise RuntimeError('error')
