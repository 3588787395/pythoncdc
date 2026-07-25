"""
Defect 11 — IF/ELIF: 裸表达式 + 语句复制 (elif 分支首条语句被复制为裸 Name)
================================================================
触发区域类型：IF/ELIF (isinstance 链)
根因初判：
    core/cfg/region_ast_generator.py `_generate_if` 在处理
    `elif isinstance(l, list) or isinstance(l, tuple):` 分支时，
    把分支首条语句 `l = l.replace(...)` 的 RHS 计算指令
    (LOAD_FAST l + LOAD_ATTR replace + ...) 错误地拆出一个
    孤立的 `l` Expr 语句放在分支开头，然后把完整的赋值语句
    再发射一次，造成「裸 l + 完整赋值」并存。
    违反「每块唯一归属」：LOAD_FAST l 应作为 `l.replace(...)`
    Call 的子节点（receiver），不应被提升为独立 Expr。

最小字节码模式（Python 3.11，elif 分支首条 store_attr/调用）：
    LOAD_FAST l
    POP_JUMP_IF_FALSE ...               # isinstance check 1
    ...
    LOAD_FAST l                         # ← 这两个 LOAD_FAST l
    LOAD_ATTR replace                   #   一个被误识别为 Expr(l)
    LOAD_CONST '.XSHE'
    LOAD_CONST '.SZ'
    CALL_METHOD 2
    STORE_FAST l                        # l = l.replace(...)
    FOR_ITER ...                        # for s in l:

反编译产物（错误，裸 l + 重复赋值）：
    elif isinstance(l, list) or isinstance(l, tuple):
        l = l.replace('.XSHE', '.SZ')
        l                                # ← 裸 Name Expr
        l = l.replace('.XSHE', '.SZ')    # ← 重复赋值
        for s in l:
            s = s.replace('.XSHE', '.SZ')
            check_stock(s)
    else:
        raise RuntimeError('error')
期望产物：
    elif isinstance(l, list) or isinstance(l, tuple):
        l = l.replace('.XSHE', '.SZ')
        for s in l:
            s = s.replace('.XSHE', '.SZ')
            check_stock(s)
    else:
        raise RuntimeError('error')

验证：python pycdc.py <this>.pyc
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
            check_stock(s)
    else:
        raise RuntimeError('error')
