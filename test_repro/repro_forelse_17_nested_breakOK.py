# Source Generated with Decompyle++ (Python version)
# File: repro_forelse_17_nested_break.pyc (Python 3.11)

__doc__ = """Repro 17: for-else with break in nested for loop

When there are nested for-else loops, the inner break's
JUMP_FORWARD target must skip the inner else block but
land inside the outer loop. The decompiler may incorrectly
set the JUMP_FORWARD target.

Original:
  for outer in data:
      for inner in outer:
          if inner == key:
              break        # breaks inner loop only
      else:
          result.append('inner_not_found')
  else:
      result.append('outer_not_found')

The inner break's JUMP_FORWARD should skip only the inner else,
not the outer else.
"""
def nested_for_else_break(data, key):
    result = []
    for outer in data:
        for inner in outer:
            if inner == key:
                break
        result.append('inner_not_found')
    else:
        result.append('outer_not_found')
        return result
code = nested_for_else_break.__code__
import dis
print('=== Nested for-else with break: JUMP_FORWARD target ===')
dis.dis(code)
