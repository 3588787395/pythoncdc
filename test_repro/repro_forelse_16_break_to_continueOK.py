# Source Generated with Decompyle++ (Python version)
# File: repro_forelse_16_break_to_continue.pyc (Python 3.11)

__doc__ = """Repro 16: for-else with break - break replaced by continue (confirmed bug!)

In Python 3.11 bytecode:
  break in for loop generates: POP_TOP + JUMP_FORWARD (past else block)
  continue in for loop generates: JUMP_BACKWARD (to FOR_ITER)

The decompiler incorrectly converts:
  POP_TOP + JUMP_FORWARD (break) -> JUMP_BACKWARD (continue)

This means:
  - The break is lost
  - The else block ALWAYS executes (because break never happens)
  - The loop always continues to the next iteration

This is the CORE for-else bug: the decompiler fails to distinguish
between break (JUMP_FORWARD past else) and the loop's natural
JUMP_BACKWARD (continue), treating both as continue.
"""
def for_else_break_replaced_by_continue(data, key):
    found = False
    for item in data:
        if item == key:
            found = True
    else:
        found = False
    return found
code = for_else_break_replaced_by_continue.__code__
import dis
print('=== BREAK REPLACED BY CONTINUE (confirmed) ===')
print('Original bytecode:')
dis.dis(code)
print()
