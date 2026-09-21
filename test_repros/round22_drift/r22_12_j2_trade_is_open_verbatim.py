# -*- coding: utf-8 -*-
# R22 锚点 12 —— J2' 语料原形（MarketTime.trade_is_open 的窗口判据逐字搬入）。
#
# 规则站点 core/cfg/region_ast_generator.py::_discover_predicate_and_chain
# 末尾 `return {'blocks': chain, 'op': 'and'}` 之前；J2' 判据：链首块若是另一个
# 纯操作数求值块（_chain_block_is_pure）前向条件跳转的落点 → 本 and 链只是
# `X or <and 链>` 的末析取支，拒绝以它重建整个 test。
#
# 语料锚点 site-packages/fly/common/market_time.pyc <module>.MarketTime.trade_is_open
#   base: seq_len orig=97 decomp=89（−8）；after: ok。
#   base 产物（D:/Temp/r22batt/tio_base.txt）第 5 行：
#     if current_dt >= '1300' and current_dt <= '1515':      ← 左析取支整半被丢
#   after 产物：
#     if current_dt >= '0915' and current_dt <= '1130' or current_dt >= '1300' and ...
# 本复现（<module>.T.open，orig=21）：base=MISMATCH decomp=13，after=MATCH。
# 类别 FIX（仅 mirror/j2p 可修）。
class T:
    def open(self, hhmm):
        if hhmm >= '0915' and hhmm <= '1130' or hhmm >= '1300' and hhmm <= '1515':
            return True
        return False
