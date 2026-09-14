# Source Generated with Decompyle++ (Python version)
# File: repro_forelse_12_swap_return.pyc (Python 3.11)

__doc__ = """Repro 12: for-else with SWAP/POP_TOP (return value optimization) - else misidentified

Original pattern from get_user_info:
  for item in csv_r:
      if item[0] == trade_id:
          # Python optimizes: return item  with SWAP/POP_TOP
          SWAP 2
          POP_TOP
          RETURN_VALUE
  else:
      fp.close()

The SWAP+POP_TOP pattern (Python 3.11 return optimization)
confuses the decompiler's for-else detection because it
doesn't see a clear JUMP_BACKWARD before the FOR_ITER target.

Original bytecode at loop end:
  264 RETURN_VALUE           <-- return in loop
  266 RETURN_VALUE           <-- dead code after return  
  268 JUMP_BACKWARD 42 (to 186)
  270 JUMP_FORWARD 43 (to 358)   <-- else block

Decompiled bytecode:
  262 RETURN_VALUE
  264 POP_TOP                  <-- wrong: should be dead code / part of else
  266 LOAD_CONST 0
  268 RETURN_VALUE             <-- extra return that shouldn't be here
  270 JUMP_BACKWARD 44 (to 184)
  272 LOAD_CONST 0             <-- else block missing, replaced by unconditional code
  274 RETURN_VALUE
"""
def for_else_swap_return(data, key):
    fp = None
    for item in data:
        if item == key:
            return item
    else:
        if fp is not None:
            fp = 'closed'
        return None
code = for_else_swap_return.__code__
import dis
print('=== for-else with SWAP/POP_TOP return: else misidentified ===')
dis.dis(code)
