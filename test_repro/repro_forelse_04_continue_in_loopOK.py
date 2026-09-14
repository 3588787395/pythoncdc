# Source Generated with Decompyle++ (Python version)
# File: repro_forelse_04_continue_in_loop.pyc (Python 3.11)

__doc__ = """Repro 4: for-else with continue in else body - else body merged with loop body

Original pattern from get_trade_list:
  for item in csv_reader:
      if strategy_type is None:
          if mode == 'custom':
              if item['status'] != '2':
                  if op_station:
                      if item['op_station'] == op_station:
                          trades.append(item)
              continue                   # <-- continue in else-if chain
          elif item['status'] != '2':
              ...
              continue
  else:                                  # <-- outer else (for-else)
      ...

Original:  FOR_ITER at 816 -> target 1524 (no else - the for loop has no else)
But the inner try-except has an else at 484 -> JUMP_FORWARD to 594
The decompiler correctly keeps the inner else but misidentifies
the outer for loop structure.

Decompiled: FOR at 416 -> target 488 (correct, no else)
But the for-else at 412 -> 484 JUMP_FORWARD -> 594 is correct in decompiled
The mismatch is in the second for loop at 816 vs 712.
"""
def for_else_with_continue(data, filter_fn):
    result = []
    for item in data:
        if filter_fn(item):
            result.append(item)
            continue
        result.append('skipped')
    else:
        result.append('completed')
        return result
code = for_else_with_continue.__code__
import dis
print('=== for-else with continue: else block handling ===')
dis.dis(code)
