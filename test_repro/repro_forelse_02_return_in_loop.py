"""Repro 2: for-else with return in loop body - else block lost

Original pattern from get_user_info:
  for item in csv_r:
      if item[0] == trade_id:
          return item
  else:                          # <-- else BLOCK MISSING
      fp.close()

Original bytecode:
  186 FOR_ITER 41 (to 270)
  268 JUMP_BACKWARD 42 (to 186)
  270 JUMP_FORWARD 43 (to 358)    <-- else block start

Decompiled bytecode:
  184 FOR_ITER 45 (to 276)
  270 JUMP_BACKWARD 44 (to 184)
  272 LOAD_CONST 0                 <-- no JUMP_FORWARD, else block missing
  274 RETURN_VALUE
"""
def for_else_return_in_loop(data, key):
    for item in data:
        if item == key:
            return item
    else:
        return None
    return 'unreachable'

code = for_else_return_in_loop.__code__
import dis
print("=== for-else with return: else block lost ===")
dis.dis(code)
