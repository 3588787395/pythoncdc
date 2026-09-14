# Source Generated with Decompyle++ (Python version)
# File: repro_forelse_03_mismatch_target.pyc (Python 3.11)

__doc__ = """Repro 3: for-else merged into post-loop code (else body runs unconditionally)

Original pattern from get_trade_status:
  for items in csv_reader:
      if len(items) > 0:
          if items[0] == trade_id:
              return items
      else:
          system_log.warning('file is empty')
          continue
  else:                              # <-- else JUMP_FORWARD target wrong
      # post-for-else code
      pass

Original bytecode:  FOR_ITER -> 598, JUMP_FORWARD 598 -> 810
Decompiled bytecode: FOR_ITER -> 598, JUMP_FORWARD 598 -> 830 (wrong target, +20 offset)

The else block body is there but the JUMP_FORWARD target is shifted,
causing the else block to include extra instructions or skip some.
"""
def for_else_mismatch_target(data, key):
    result = []
    for item in data:
        if item == key:
            result.append(item)
            continue
    else:
        result.append('loop_completed')
        result.append('after_loop')
        return result
code = for_else_mismatch_target.__code__
import dis
print('=== for-else: JUMP_FORWARD target mismatch ===')
dis.dis(code)
