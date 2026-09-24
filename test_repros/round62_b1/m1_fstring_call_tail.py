# -*- coding: utf-8 -*-
"""R62 diag: minimal repro of the f-string-as-call-argument tail collapse.

Mirrors TradeLiveBroker.fund_transfer / market_fund_transfer tails:
each arm of an if/else ends with `log.error(f"<ternary>{call}</ternary>...")`
followed by `return <const>`, and the else arm likewise.  The f-string is the
*argument of an expression-statement call*, so the value it builds is consumed
by CALL+POP_TOP before the block's RETURN_VALUE.
"""

strategy_log = None


def fund_like(error_dict, trans_direction, exchange_type, occur_balance):
    if error_dict.get('error_no') != 0:
        strategy_log.error(f"{'IN' if trans_direction == '0' else 'OUT'}fast{'A' if exchange_type == '1' else 'B'}fail, reason: {error_dict.get('error_info')}")
        return False
    else:
        strategy_log.info(f"ok {occur_balance} amount")
        return True
