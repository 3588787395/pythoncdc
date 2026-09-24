# -*- coding: utf-8 -*-
"""R62 diag repro 2: both if-arms end with an f-string call whose then-arm
contains a call-valued interpolation.  Mirrors fund_transfer's tail exactly
(then: two ternaries + `{error_dict.get('error_info')}`; else: two ternaries +
`{occur_balance}`).
"""

strategy_log = None


def both_arms(error_dict, trans_direction, exchange_type, occur_balance):
    if error_dict.get('error_no') != 0:
        strategy_log.error(f"{'IN' if trans_direction == '0' else 'OUT'}fast{'A' if exchange_type == '1' else 'B'}fail, reason: {error_dict.get('error_info')}")
        return False
    else:
        strategy_log.info(f"{'IN' if trans_direction == '0' else 'OUT'}fast{'A' if exchange_type == '1' else 'B'}ok {occur_balance}")
        return True
