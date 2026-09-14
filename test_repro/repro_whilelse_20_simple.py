"""Repro 20: while-else with break - else block dropped

Python 3.11 while-else bytecode structure:
  while condition:
      ...
      if exit_condition:
          break        # JUMP_FORWARD past else block
      ...
  else:
      ...              # runs only if loop exhausted (no break)

The while-else has a different bytecode pattern from for-else:
  - for-else: FOR_ITER exhaustion -> JUMP_FORWARD (to else body)
  - while-else: POP_JUMP_BACKWARD_IF_TRUE back-edge, then else body

For while-else in Python 3.11:
  condition check -> POP_JUMP_FORWARD_IF_FALSE (to else body / exit)
  loop body -> POP_JUMP_BACKWARD_IF_TRUE (back to condition)
  else body -> (after loop condition fails)
  after else -> JUMP_FORWARD or next instruction

The decompiler may not recognize the while-else because there's
no FOR_ITER to mark the loop boundary.
"""
def while_else_simple(limit, exit_val):
    count = 0
    while count < limit:
        if count == exit_val:
            break
        count += 1
    else:
        count = -1
    return count

code = while_else_simple.__code__
import dis
print("=== while-else with break ===")
dis.dis(code)
