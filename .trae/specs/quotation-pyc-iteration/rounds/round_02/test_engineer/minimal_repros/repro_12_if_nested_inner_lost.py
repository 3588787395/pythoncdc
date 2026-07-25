"""
Defect 12 (R1 残留，部分已修) — IF：嵌套 `if A: S; if B:` 内层 if 丢失（R1 语句提升已解除）
================================================================
关联 R1 repro：repro_12_if_nested_merge_and_hoist（R1：S1/S2 提升出 if + 嵌套合并为 `A and B`）。

R2 复现状态：**语句提升已解除，但内层 if 丢失（形态演化）**。
  R1 表现：`stock_list = [stocks]` / `check_stocks(...)` 被提升出 if；嵌套 `if filled:` 合并为 `if A and B:`
  R2 表现（quotation.pyc::get_valuation_info line 2219-2223）：
        def get_valuation_info(count, date, stocks, filled=False):
            if isinstance(stocks, str):
                stock_list = [stocks]          # ← R1 提升已解除（回到 if 内）
                check_stocks(stock_list)       # ← R1 提升已解除
                date = str(date)
    —— R1 的语句提升 + 嵌套合并已解除，但内层 `if filled: trading_days = ...; return index`
       整段丢失，函数末尾 `return {}` 也丢失（get_valuation_info orig=121 instrs → r2=108）。

触发区域类型：IF (嵌套 if) + 内层 if 丢失
根因初判：
    `core/cfg/region_analyzer.py::_identify_if_regions` 在归约 `if A: S1; S2; if B: body`
    时，外层 if 的 then-块归约已正确（S1/S2 留在 if 内），但内层 `if B:`（POP_JUMP_IF_FALSE）
    的整个 then-块被错误吸收为不可达子区域，导致内层 if 与后续 return 丢失。
    违反「自底向上归约」：内层 IfRegion 应作为外层 If.body 的子节点保留。

最小字节码模式（Python 3.11）：
    LOAD_GLOBAL isinstance / LOAD_FAST stocks / LOAD_GLOBAL str
    CALL / POP_JUMP_IF_FALSE to <else>            # if isinstance(stocks, str):
      <S1: stock_list = [stocks]>
      <S2: check_stocks(stock_list)>
      LOAD_FAST filled
      POP_JUMP_IF_FALSE to <end>                  # if filled:   ← 内层 if 丢失
        <body: trading_days = ...; return index>
      JUMP_FORWARD to <end>
    <else>:
      LOAD_CONST {} / RETURN_VALUE
    <end>:

R2 反编译产物（错误，内层 if + return 丢失）：
    def get_valuation_info(count, date, stocks, filled=False):
        if isinstance(stocks, str):
            stock_list = [stocks]
            check_stocks(stock_list)
            date = str(date)
期望产物：
    def get_valuation_info(count, date, stocks, filled=False):
        if isinstance(stocks, str):
            stock_list = [stocks]
            check_stocks(stock_list)
            if filled:
                trading_days = get_trading_days()
                index = trading_days[-count:]
                return index
        return {}

验证：python pycdc.py <this>.pyc  # 观察内层 if filled 丢失
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
