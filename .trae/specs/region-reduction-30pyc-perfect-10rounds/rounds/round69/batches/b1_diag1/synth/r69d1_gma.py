# r69diag1 synth witness: shared branch body double-emitted as elif_final_else.
# Shape matches trade_live_broker.get_max_amount: the same `max_amount = ...`
# block is the true-target of an `or` condition chain AND the then-block of
# the nested if, so it must be emitted exactly ONCE (source used `or`).
def r69d1_gma(error_no, entrust_bs, entrust_type, result):
    if error_no != 0:
        return 'err'
    elif (entrust_bs == '1' and entrust_type in ('6', '7', '9')) or (entrust_bs == '2' and entrust_type == '7'):
        max_amount = int(float(result[0].get('enable_buy_amount')))
    else:
        max_amount = int(float(result[0].get('enable_amount')))
    return max_amount
