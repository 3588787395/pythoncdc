# Source Generated with Decompyle++ (Python version)
# File: repro_forelse_11_multiple_exits.pyc (Python 3.11)

__doc__ = """Repro 11: for-else with continue and break - else block lost due to multiple exits

Pattern from get_trade_list's inner for loop:
  for item in csv_reader:
      if strategy_type is None:
          if mode == 'custom':
              ...
              continue
          elif item['status'] != '2':
              ...
              continue
      elif strategy_type == 'trade':
          ...
          continue
      elif strategy_type == 'current_trade':
          ...
          continue
      elif item['status'] in ('0', '5') and ...:
          trades.append(item)
          continue
  else:
      # filter trades by channel_type
      trades = [item for item in trades if item.get('channel_type') == 'app']

The original has TWO for-else patterns:
1. Inner for-else at 412 -> 484 JUMP_FORWARD -> 594 (correctly decompiled)
2. Outer for-else at 1606 -> 1668 JUMP_FORWARD -> ... (correctly decompiled)

BUT the main for loop at 816 -> 1524 has NO else in original,
while in decompiled at 712 -> 1426 also has no else. That's correct.

The actual bug is: the first for-else (412->484) is correctly
decompiled, but the exception handler structure after it is wrong.
The JUMP_FORWARD from 484->594 in original becomes a different
flow in decompiled (488->NOP, then os.path.exists check).
"""
def for_else_multiple_exits(data, filter_type, mode=None):
    result = []
    for item in data:
        if filter_type is None:
            if mode == 'custom':
                if item != 'skip':
                    result.append(item)
            elif item != 'exclude':
                result.append(item)
            else:
                continue
        elif filter_type == 'active':
            if item in ('a', 'b'):
                result.append(item)
        elif item == 'target':
            result.append(item)
        else:
            continue
    else:
        result = [x for x in result if x != 'removed']
        return result
code = for_else_multiple_exits.__code__
import dis
print('=== for-else with multiple exit paths ===')
dis.dis(code)
