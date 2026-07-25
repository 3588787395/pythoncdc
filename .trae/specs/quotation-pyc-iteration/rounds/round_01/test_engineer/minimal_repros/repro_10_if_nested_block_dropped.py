"""
Defect 10 — IF: 整个 `if A:` 嵌套 if/elif/elif 块被完全丢弃 + `and X is None` 条件被截断
================================================================
触发区域类型：IF (if/elif/elif 嵌套) + BOOLOP (and) + IS_OP (is None)
根因初判：
    core/cfg/region_analyzer.py `_identify_if_regions` 在归约
    `if A:` (POP_JUMP_IF_NONE) 内嵌套 `if B: ... elif C: ... elif D: ...`
    的复杂结构时，把外层 if 的整个 then-块（含嵌套 if/elif/elif）
    错误归约为不可达 / 被吸收的子区域，导致整段语句丢失；
    紧随其后的 `if E and F is None:` (其中 F is None 走
    POP_JUMP_IF_NOT_NONE) 的条件也被截断为只剩 `if E:`，
    丢失 `and F is None` 子句。
    违反「自底向上归约」：嵌套 IfRegion 应作为外层 If.body 的
    子节点保留，不应被丢弃。

最小字节码模式（Python 3.11）：
    LOAD_FAST security
    POP_JUMP_FORWARD_IF_NONE to <after-if1>     # if security is not None:
      LOAD_GLOBAL len / LOAD_FAST security / COMPARE_OP == / POP_JUMP_IF_FALSE
      <if len==0 body>
      LOAD_GLOBAL isinstance / ... / POP_JUMP_IF_FALSE
      <elif isinstance str body>
      LOAD_FAST fq / LOAD_CONST 'dypre' / COMPARE_OP == / POP_JUMP_IF_FALSE
      <elif fq=='dypre' body>
    <after-if1>:
    LOAD_GLOBAL frequency / CONTAINS_OP / POP_JUMP_IF_FALSE
    LOAD_GLOBAL query_date / POP_JUMP_IF_NOT_NONE   # and query_date is None
    <if-body>

反编译产物（错误，整段 if 丢失 + 条件截断）：
    @check_arg
    def get_price(...):
        if frequency not in OVER_WEEK_FREQUENCY:        # ← 缺 `and query_date is None`
            now_dt = datetime.now()
            query_date = now_dt
        else:
            query_date = datetime.strptime(query_date, '%Y%m%d')
        return security
期望产物：
    @check_arg
    def get_price(...):
        ClearAllCache()
        is_string = False
        if security is not None:                        # ← 整段被丢
            if len(security) == 0:
                strategy_log.error('security cannot be empty')
            elif isinstance(security, str):
                is_string = True
                security = [security]
            elif fq == 'dypre':
                fq = 'pre'
        if frequency not in OVER_WEEK_FREQUENCY and query_date is None:
            now_dt = datetime.now()
            query_date = now_dt
        else:
            query_date = datetime.strptime(query_date, '%Y%m%d')
        return security

验证：python pycdc.py <this>.pyc
"""
def check_arg(f):
    return f

@check_arg
def get_price(security, start_date=None, end_date=None, frequency='daily', fields=None, fq=None, count=None, is_dict=False):
    ClearAllCache()
    is_string = False
    if security is not None:
        if len(security) == 0:
            strategy_log.error('security cannot be empty')
        elif isinstance(security, str):
            is_string = True
            security = [security]
        elif fq == 'dypre':
            fq = 'pre'
    if frequency not in OVER_WEEK_FREQUENCY and query_date is None:
        now_dt = datetime.now()
        query_date = now_dt
    else:
        query_date = datetime.strptime(query_date, '%Y%m%d')
    return security
