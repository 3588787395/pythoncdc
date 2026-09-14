"""Repro 1: for-else with break - else block completely missing in decompilation

Original pattern from get_trade_list:
  for item in csv_reader:
      if condition:
          trades.append(item)
  else:                          # <-- THIS else BLOCK IS MISSING IN DECOMPILED OUTPUT
      os.path.exists(file)

Original bytecode: FOR_ITER -> JUMP_FORWARD (else clause)
Decompiled bytecode: FOR_ITER -> no JUMP_FORWARD (else clause missing)
"""
def for_else_missing(items, target):
    result = []
    for item in items:
        if item == target:
            result.append(item)
    else:
        result.append('not_found')
    return result

# Expected: if loop completes without break, 'not_found' is appended
# Bug: decompiler drops the else block entirely
code = for_else_missing.__code__
import dis
print("=== for-else with break: else block missing ===")
dis.dis(code)
print()
print("co_varnames:", code.co_varnames)
