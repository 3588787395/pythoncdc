# Source Generated with Decompyle++ (Python version)
# File: repro_whilelse_15_if_after.pyc (Python 3.11)

__doc__ = """Repro 15: while-else where else is followed by if statement

Original pattern from kill_trade_process:
  while count < KILL_TRADE_PROCESS_ATTEMPTS:
      process_id = open(lock_path).readline()
      if process_id != '':
          break
      time.sleep(0.001)
      count += 1
  else:                                    # <-- while-else
      JUMP_FORWARD 70 (to 3270)
  # Code after else:
  if process_id is not None:
      process_id = process_id.replace(...)
      ...

The decompiler fails to distinguish:
1. The while-else block (JUMP_FORWARD from while exhaustion)
2. The code that follows the else block

In the decompiled output, the JUMP_FORWARD target is correct
(3048 -> 3190), but the else body is not properly delineated.
The code after the else (if process_id is not None) gets
absorbed into the else block or the exception handler.
"""
def while_else_if_after(limit, check):
    count = 0
    result = None
    while count < limit:
        result = count
        if result == check:
            break
        count += 1
    result = -1
    if result is not None:
        result = str(result)
    return result
code = while_else_if_after.__code__
import dis
print('=== while-else followed by if: else boundary wrong ===')
dis.dis(code)
