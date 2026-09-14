"""Repro 24: for-else where else body is just assignment - else silently dropped

When the else block is very simple (just an assignment), the
decompiler may silently drop it because it can't distinguish
the else block's JUMP_FORWARD from a normal flow instruction.

Pattern from get_trade_list:
  for item in trades:
      backtest_content_id = item.get('backtestContentId')
      if backtest_content_id:
          trades_dict[backtest_content_id] = item
  else:
      trades = list(trades_dict.values())

The else block (trades = list(trades_dict.values())) is
the ONLY code between the for loop and the except handler.
The JUMP_FORWARD from the else must skip the except handler.
"""
def for_else_simple_assignment(data):
    result_dict = {}
    for item in data:
        key = item.get('id')
        if key:
            result_dict[key] = item
    else:
        data = list(result_dict.values())
    return data

code = for_else_simple_assignment.__code__
import dis
print("=== for-else with simple assignment in else ===")
dis.dis(code)
