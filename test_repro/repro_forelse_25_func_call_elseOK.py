# Source Generated with Decompyle++ (Python version)
# File: repro_forelse_25_func_call_else.pyc (Python 3.11)

__doc__ = """Repro 25: for-else where else body is a function call - else becomes unconditional

When the else body is just a function call (like a logging call),
the decompiler may treat it as post-loop code that runs
unconditionally rather than as part of the else clause.

Pattern from get_trade_status:
  for items in csv_reader:
      if len(items) > 0 and items[0] == trade_id:
          return items
      else:
          system_log.warning('file is empty')
          continue
  else:
      # This else block is separated from the for by an except handler
      pass

The continue inside the else-if chain confuses the for-else
boundary detection.
"""
def for_else_func_call_else(data, key):
    import logging
    log = logging.getLogger()
    for item in data:
        if item == key:
            return item
        log.warning('skip')
    else:
        log.info('not_found')
        return None
code = for_else_func_call_else.__code__
import dis
print('=== for-else with function call in else body ===')
dis.dis(code)
