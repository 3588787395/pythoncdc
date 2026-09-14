"""Repro 9: while-else inside try-except - else absorbed by except

Original pattern from kill_trade_process (the actual code):
  try:
      while count < KILL_TRADE_PROCESS_ATTEMPTS:
          process_id = open(lock_path).readline()
          if process_id != '':
              break
          time.sleep(0.001)
          count += 1
  except BaseException:
      process_id = None

In the original, the while loop has NO else clause (the JUMP_FORWARD
after while exhaustion goes to except handler area). But in the 
decompiled version, the structure is preserved differently because
the decompiler doesn't properly distinguish while-else from the
gap between while-end and except-handler.

The decompiler incorrectly generates extra return statements
after the while loop because it can't tell that the JUMP_FORWARD
target after the while loop is just the continuation of normal
flow, not an else block.
"""
def while_else_in_try(limit):
    result = 0
    try:
        count = 0
        while count < limit:
            result += count
            if result > 5:
                break
            count += 1
        else:
            result = -1
    except Exception:
        result = -2
    return result

code = while_else_in_try.__code__
import dis
print("=== while-else inside try-except ===")
dis.dis(code)
