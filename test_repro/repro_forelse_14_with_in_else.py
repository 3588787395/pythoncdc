"""Repro 14: for-else where else body contains with statement

Original pattern from kill_trade_process (for-else at 1540->2462):
  for running_trade_id in trade_id_list:
      ...
      if len(response) > 0:
          write_info.append(...)
          count += 1
          continue
      app_log.error(...)
      continue
  else:                                       # <-- for-else
      with FileLock(sim_trading_path):
          FileIO(sim_trading_path).write(...)

Original bytecode:
  2462 JUMP_FORWARD -> else block (with FileLock)
  
Decompiled: The for loop at 1540 has no else in decompiled output.
The else body (with FileLock) appears as unconditional code after the for loop.

This is because the decompiler doesn't recognize that the JUMP_FORWARD
after FOR_ITER exhaustion is an else clause when the else body
contains a with statement (which has its own exception handling).
"""
def for_else_with_statement(data):
    result = []
    for item in data:
        if item > 0:
            result.append(item)
            continue
        result.append('skipped')
        continue
    else:
        with open('test.txt', 'w') as f:
            f.write(str(result))
    return result

code = for_else_with_statement.__code__
import dis
print("=== for-else with with-statement in else body ===")
dis.dis(code)
