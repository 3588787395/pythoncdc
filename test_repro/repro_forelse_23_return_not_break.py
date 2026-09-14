"""Repro 23: for-else with return instead of break - else block lost

When the for-else loop uses return instead of break to exit,
the return generates different bytecode (RETURN_VALUE or
SWAP+POP_TOP+RETURN_VALUE in Python 3.11).

The decompiler may not recognize that return also prevents
the else block from executing, and may drop the else block
or merge it with post-loop code.

From get_user_info original bytecode:
  214 LOAD_FAST item
  216 SWAP 2
  218 POP_TOP
  220 LOAD_FAST fp
  222 POP_JUMP_FORWARD_IF_NONE 21 (to 266)
  224 LOAD_FAST fp
  ...fp.close()...
  264 RETURN_VALUE        <-- return inside loop (not break)
  266 RETURN_VALUE        <-- dead code
  268 JUMP_BACKWARD 42    <-- loop continue
  270 JUMP_FORWARD 43     <-- else block start

Decompiled: else block missing, replaced by unconditional code
"""
def for_else_return_not_break(data, key):
    fp = None
    for item in data:
        if item == key:
            return item
    else:
        fp = 'closed'
    return fp

code = for_else_return_not_break.__code__
import dis
print("=== for-else with return instead of break ===")
dis.dis(code)
