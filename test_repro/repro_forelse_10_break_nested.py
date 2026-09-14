"""Repro 10: for-else with break inside nested if - else clause dropped

This is the most common pattern in trade_info_utils.py.
When the for loop body has a break inside a conditional,
the decompiler fails to recognize the for-else structure.

Original bytecode pattern:
  FOR_ITER -> target
  ...loop body with conditional break...
  JUMP_BACKWARD (loop back-edge)
  JUMP_FORWARD -> else_start   <-- this marks the else clause
  ...else body...
  JUMP_FORWARD -> after_else

The decompiler sees:
  FOR_ITER -> target
  ...loop body...
  JUMP_BACKWARD (loop back-edge)
  ...else body runs unconditionally... <-- else marker (JUMP_FORWARD) missing
"""
def for_else_break_nested(data, key):
    found = False
    for item in data:
        if item == key:
            found = True
            break
    else:
        found = False
    return found

code = for_else_break_nested.__code__
import dis
print("=== for-else with break in nested if: else dropped ===")
dis.dis(code)
