"""
Defect R3-12 (R1/R2 残留) — IF：嵌套 `if A: S; if B:` 内层 if 丢失（合并为 A and B + 语句提升）
================================================================
关联 R1/R2 repro：repro_12_if_nested_merge_and_hoist / repro_12_if_nested_inner_lost

R3 复现状态：**R2 未修复，quotation.pyc::get_valuation_info 仍复现（且函数整体被截断到 21 instr，
            orig 121 → new 21，内层 if 与函数末尾 return 整段丢失）**。
  R3 表现（quotation.pyc::get_valuation_info line 2216-2221）：
        def get_valuation_info(count, date, stocks, filled=False):
            if isinstance(stocks, str):
                stock_list = [stocks]
            elif isinstance(stocks, Iterable):
                stock_list = stocks
            return {}
        —— 内层 `if filled: trading_days = ...; return index` 与外层 `if isinstance:` 的 then-块
           整段丢失，函数末尾 `return {}` 提前（与 repro_14 截断同源）。
  最小复现暴露另一种形态：外层 if 与内层 if 被合并为 `if A and B:`，
  且 then-块语句（stock_list = [stocks]; check_stocks(...)）被提升到 if 之前。

触发区域类型：IF（嵌套 if）+ 内层 if 丢失 / 合并 + 语句提升
根因初判：
    `region_ast_generator.py::_identify_if_regions` 在归约 `if A: S1; S2; if B: body` 时，
    把外层 if 与内层 if 合并为 `if A and B:`，并把 S1/S2 提升出 if 块；
    在更复杂场景下（quotation.pyc::get_valuation_info），elif 链后整段内层 if 与 return 丢失。
    违反「自底向上归约」+「嵌套即抽象节点」。

最小字节码模式（Python 3.11）：
    LOAD_GLOBAL isinstance
    LOAD_FAST stocks
    LOAD_GLOBAL str
    CALL
    POP_JUMP_IF_FALSE                  # if isinstance(stocks, str):
      LOAD_FAST stocks
      BUILD_LIST
      STORE_FAST stock_list            #   stock_list = [stocks]
      LOAD_GLOBAL check_stocks
      LOAD_FAST stock_list
      CALL
      POP_TOP                          #   check_stocks(stock_list)
      LOAD_FAST filled
      POP_JUMP_IF_FALSE                #   if filled:   ← 内层 if 被合并/丢失
        LOAD_GLOBAL get_trading_days
        CALL
        STORE_FAST trading_days
        ...
        RETURN_VALUE
    LOAD_CONST {}
    RETURN_VALUE                       # return {}

R3 反编译产物（错误，最小复现形态）：
    def get_valuation_info(count, date, stocks, filled=False):
        stock_list = [stocks]              # ← 提升出 if
        check_stocks(stock_list)           # ← 提升出 if
        if isinstance(stocks, str) and filled:    # ← 外层 + 内层合并
            trading_days = get_trading_days()
            index = trading_days[-count:]
            return index
        else:
            return {}

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

验证：
    $ python3 -c "import py_compile; py_compile.compile('repro_03_if_nested_inner_lost.py', 'repro_03_if_nested_inner_lost.pyc', doraise=True)"
    $ python pycdc.py repro_03_if_nested_inner_lost.pyc
    # 观察外层 if 与内层 if 合并为 A and B，且 then-块语句被提升到 if 之前
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
