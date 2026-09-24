# Source Generated with Decompyle++ (Python version)
# File: m2_both_arms.pyc (Python 3.11)

__doc__ = """R62 diag repro 2: both if-arms end with an f-string call whose then-arm
contains a call-valued interpolation.  Mirrors fund_transfer's tail exactly
(then: two ternaries + `{error_dict.get('error_info')}`; else: two ternaries +
`{occur_balance}`).
"""
strategy_log = None
def both_arms(error_dict, trans_direction, exchange_type, occur_balance):
    if error_dict.get('error_no') != 0:
        'IN' if trans_direction == '0' else 'OUT'
    else:
        'IN' if trans_direction == '0' else 'OUT'
