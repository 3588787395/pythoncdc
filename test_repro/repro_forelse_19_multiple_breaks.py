"""Repro 19: for-else with multiple break points

When a for-else loop has multiple break points (different conditions),
each break generates a separate POP_TOP + JUMP_FORWARD instruction.
The decompiler must correctly identify ALL of them as breaks that
skip the else block, not as continues.

Original pattern from trade_operation:
  for items in csv_reader:
      if items[0] in trade_id_list:
          if operation == 'start':
              items[2] = '0'
              operation = 'restart'
          if operation == 'stop':
              items[2] = '1'
          if operation == 'delete':
              items[2] = '2'
              delete_write_info.append(items)
              continue                    # <-- continue (not break)
          elif operation == 'pause':
              items[2] = '3'
          if operation == 'reload':
              items[2] = '4'
          # no break here, just falls through
      write_info.append(items)
      continue                           # <-- continue
  # No else block in this specific case
"""
def for_else_multiple_breaks(data, key1, key2):
    result = []
    for item in data:
        if item == key1:
            result.append('found1')
            break
        if item == key2:
            result.append('found2')
            break
    else:
        result.append('not_found')
    return result

code = for_else_multiple_breaks.__code__
import dis
print("=== for-else with multiple breaks ===")
dis.dis(code)
