"""Repro 22: for-else with try-except INSIDE loop body - break in try block

When a for-else loop has a try-except block inside the loop body,
and the break is inside the try block, the break's JUMP_FORWARD
must skip both the except handler AND the else block.

Original pattern from check_and_update_trade:
  for line in csv_reader:
      try:
          if condition:
              break              # break inside try
      except:
          pass
  else:
      # handle no match

The break's JUMP_FORWARD target must skip the except handler
and land past the else block. The decompiler may set the
target incorrectly.
"""
def for_else_break_in_try(data, key):
    result = []
    for item in data:
        try:
            if item == key:
                result.append(item)
                break
        except ValueError:
            result.append('value_error')
    else:
        result.append('not_found')
    return result

code = for_else_break_in_try.__code__
import dis
print("=== for-else with break inside try block ===")
dis.dis(code)
