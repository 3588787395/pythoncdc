# Source Generated with Decompyle++ (Python version)
# File: repro_whilelse_08_break.pyc (Python 3.11)

__doc__ = """Repro 8: while-else - else block merged with post-while code

Original pattern from kill_trade_process:
  while count < KILL_TRADE_PROCESS_ATTEMPTS:
      process_id = open(lock_path).readline()
      if process_id != '':
          break
      time.sleep(0.001)
      count += 1
  else:                                       # <-- while-else
      # process_id is None after loop exhausted
      pass

Original bytecode:
  2948 LOAD_FAST count
  2950 LOAD_GLOBAL KILL_TRADE_PROCESS_ATTEMPTS
  2962 COMPARE_OP <
  2968 POP_JUMP_FORWARD_IF_FALSE 79 (to 3128)  <-- while condition
  ...loop body...
  3126 POP_JUMP_BACKWARD_IF_TRUE 79 (to 2970)  <-- while back-edge
  3128 JUMP_FORWARD 70 (to 3270)               <-- while-else block

Decompiled bytecode:
  Same while loop structure but the else block at 3128->3270 is
  treated as if it's part of the except handler below, not as
  a while-else clause. The JUMP_FORWARD target at 3048->3190
  skips into the except handler instead of the else block.

The while-else is not recognized and its body is treated as
regular post-loop code.
"""
def while_else_break(count_limit):
    count = 0
    result = None
    while count < count_limit:
        result = count * 2
        if result > 10:
            break
        count += 1
    else:
        result = -1
    return result
code = while_else_break.__code__
import dis
print('=== while-else with break: else block merged ===')
dis.dis(code)
