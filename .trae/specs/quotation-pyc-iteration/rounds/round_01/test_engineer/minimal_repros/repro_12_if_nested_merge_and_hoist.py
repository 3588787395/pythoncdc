"""
Defect 12 — IF: 嵌套 `if A: if B:` 被错误合并为 `if A and B:`，且外层 if 块前的语句被提升到 if 之外
================================================================
触发区域类型：IF (嵌套 if)
根因初判：
    core/cfg/region_analyzer.py `_identify_if_regions` 在归约
    `if A: S1; S2; if B: body` 时，把外层 if 的 then-块中的
    顺序语句 S1/S2 错误提升到 if 之外（违反「每块唯一归属」：
    S1/S2 的 LOAD/CALL/STORE 指令应归 if.then 块），再把
    外层 `if A:` 与内层 `if B:` 合并为 `if A and B:`，
    改变了控制流语义（原 `not A` 分支会跳过 S1/S2，合并后
    S1/S2 在 if 之外，`not A` 也会执行 S1/S2）。
    与 repro_06 互为反向缺陷：repro_06 把 `if A and B:` 拆成
    嵌套 if；本缺陷把嵌套 if 合并成 `if A and B:`。

最小字节码模式（Python 3.11）：
    LOAD_GLOBAL isinstance / LOAD_FAST stocks / LOAD_GLOBAL str
    CALL / POP_JUMP_IF_FALSE to <else>            # if isinstance(stocks, str):
      <S1: stock_list = [stocks]>                 # ← 被错误提升到 if 之外
      <S2: check_stocks(stock_list)>              # ← 被错误提升到 if 之外
      LOAD_FAST filled
      POP_JUMP_IF_FALSE to <else>                 # if filled:
        <body: trading_days = ...; return index>
      JUMP_FORWARD to <end>
    <else>:
      LOAD_CONST {} / RETURN_VALUE
    <end>:

反编译产物（错误，语句提升 + 嵌套合并）：
    stock_list = [stocks]                          # ← 被提升出 if
    check_stocks(stock_list)                       # ← 被提升出 if
    if isinstance(stocks, str) and filled:         # ← 嵌套 if 被合并
        trading_days = get_trading_days()
        index = trading_days[-count:]
        return index
    else:
        return {}
期望产物：
    if isinstance(stocks, str):
        stock_list = [stocks]
        check_stocks(stock_list)
        if filled:
            trading_days = get_trading_days()
            index = trading_days[-count:]
            return index
    return {}

验证：python pycdc.py <this>.pyc
"""
def get_valuation_info(count, date, stocks, filled=False):
    if isinstance(stocks, str):
        stock_list = [stocks]
        check_stocks(stock_list)
        if filled:
            trading_days = get_trading_days()
            index = trading_days[-count:]
            return index
    return {}
