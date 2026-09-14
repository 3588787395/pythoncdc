"""Repro 7: for-else with nested if-elif-else chain - else block collapsed

Original pattern from get_history_common:
  if frequency != '1d':
      for _field in fields:
          if _field in DAILY_SUPPORT_FIELDS:
              strategy_log.info(...)
              return OrderedDict()
      else:                               # <-- for-else
          if 'datetime' not in fields:
              fields = ['datetime'] + fields
          # continue with processing
  else:
      # different handling for daily

Original bytecode:
  818 FOR_ITER -> 920
  918 JUMP_BACKWARD (loop body end)
  920 JUMP_FORWARD 88 -> 1118 (else block)
  922-938: else body (check datetime, modify fields)

Decompiled bytecode:
  824 FOR_ITER -> 926
  924 JUMP_BACKWARD (loop body end)
  926: No JUMP_FORWARD! Instead directly:
  926 LOAD_CONST 'datetime'
  928 BUILD_LIST 1
  930 LOAD_FAST fields
  932 BINARY_OP +
  936 STORE_FAST fields

The for-else's JUMP_FORWARD is missing, else body runs unconditionally.
The original else block contained: if 'datetime' not in fields: fields = ['datetime'] + fields
But decompiled it becomes: fields = ['datetime'] + fields (always, no condition)
"""
def for_else_nested_if_elif(data, check_fn):
    result = []
    if len(data) > 0:
        for item in data:
            if check_fn(item):
                return [item]
        else:
            if 'default' not in result:
                result = ['default'] + result
    else:
        result.append('empty')
    return result

code = for_else_nested_if_elif.__code__
import dis
print("=== for-else with nested if-elif: else block collapsed ===")
dis.dis(code)
