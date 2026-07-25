"""
Defect 10 (R1 残留，已演化) — IF/FUNCTION_DEF：函数体内 `if A and B is None:` 整段泄漏为下一函数的 `@((...))` 装饰器
================================================================
关联 R1 repro：repro_10_if_nested_block_dropped（R1：整段 if 丢失 + `and X is None` 截断）。

R2 复现状态：**复现（形态演化，跨函数泄漏）**。
  R1 表现：`if security is not None:` 整段嵌套 if/elif/elif 丢失；`and query_date is None` 截断
  R2 表现（quotation.pyc::get_price line 756-767）：
    —— `if security is not None:` 嵌套 if/elif/elif 已恢复（R1 残留部分解除）；
       但紧随其后的 `if frequency not in OVER_WEEK_FREQUENCY and query_date is None:`
       整段从 get_price 泄漏，退化为下一函数 get_history 的装饰器
       `@(('1d', None, None, None, False, False, None, 'nan', False))`
       （即 get_history 的 defaults 元组被误作装饰器，且 if 块整段丢失）。
  另：get_price 函数末尾无 return，函数体在 `elif fq == 'dypre': fq = 'pre'` 后被截断。

触发区域类型：IF (if A and B is None) + FUNCTION_DEF (defaults 误作装饰器)
根因初判：
    `core/cfg/region_analyzer.py::_identify_if_regions` 在归约 `if A and B is None:`
    （A 走 CONTAINS_OP + POP_JUMP_IF_FALSE，B is None 走 POP_JUMP_IF_NOT_NONE）
    时，把该 if 块的指令与紧随其后的 MAKE_FUNCTION defaults 元组错误归并，
    导致 if 块丢失、defaults 元组被发射为 `@((...))` 装饰器。
    违反「每块唯一归属」+「自底向上归约」。

最小字节码模式（Python 3.11）：
    <get_price body>:
      LOAD_FAST security
      POP_JUMP_IF_NONE to <after-if1>          # if security is not None:
        <nested if/elif/elif>
      <after-if1>:
      LOAD_GLOBAL frequency / CONTAINS_OP / POP_JUMP_IF_FALSE
      LOAD_GLOBAL query_date / POP_JUMP_IF_NOT_NONE   # and query_date is None
      <if-body>
    <模块级>:
      LOAD_CONST ('1d', None, ...)             # get_history defaults 元组
      LOAD_CONST <code get_history>
      MAKE_FUNCTION defaults
      → R2 误把 defaults 元组发射为 @((...)) 装饰器

R2 反编译产物（错误）：
    def get_price(...):
        ...
        elif fq == 'dypre':
            fq = 'pre'
    @(('1d', None, None, None, False, False, None, 'nan', False))
    def get_history(count, frequency='1d', ...):
        ...
期望产物：
    def get_price(...):
        if security is not None:
            if len(security) == 0: ...
            elif isinstance(security, str): ...
            elif fq == 'dypre': fq = 'pre'
        if frequency not in OVER_WEEK_FREQUENCY and query_date is None:
            now_dt = datetime.now()
            query_date = now_dt
        else:
            query_date = datetime.strptime(query_date, '%Y%m%d')
        return security
    def get_history(count, frequency='1d', ...):
        ...

验证：python pycdc.py <this>.pyc  # 观察 if 块泄漏为下一函数 @((...)) 装饰器
"""
def get_price(security, frequency='daily', fq=None, query_date=None):
    if security is not None:
        if len(security) == 0:
            log.error('empty')
        elif isinstance(security, str):
            security = [security]
        elif fq == 'dypre':
            fq = 'pre'
    if frequency not in OVER_WEEK_FREQUENCY and query_date is None:
        query_date = datetime.now()
    else:
        query_date = datetime.strptime(query_date, '%Y%m%d')
    return security
