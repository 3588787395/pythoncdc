"""Repro 18: for-else where loop body only has if-break (simplest case)

The simplest possible for-else pattern. In Python 3.11:
  for item in data:
      if item == key:
          break
  else:
      result = 'not_found'

Original bytecode:
  FOR_ITER -> target
  ...if condition: POP_TOP + JUMP_FORWARD (break, skip else)
  JUMP_BACKWARD (loop continue)
  else: LOAD_CONST 'not_found' + STORE_FAST

The decompiler may:
  1. Drop the break entirely (convert to continue)
  2. Drop the else block
  3. Set wrong JUMP_FORWARD target
"""
def simple_for_else_break(data, key):
    for item in data:
        if item == key:
            break
    else:
        return 'not_found'
    return 'found'

code = simple_for_else_break.__code__
import dis
print("=== Simplest for-else-break ===")
dis.dis(code)
