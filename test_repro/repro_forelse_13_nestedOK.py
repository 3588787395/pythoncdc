# Source Generated with Decompyle++ (Python version)
# File: repro_forelse_13_nested.pyc (Python 3.11)

__doc__ = """Repro 13: Nested for-else - inner else preserved, outer else lost

Original pattern from get_price_common:
  for stock in symbols:
      ...
      for _field in fields:
          if _field in DAILY_SUPPORT_FIELDS:
              return OrderedDict()
      else:                           # <-- inner for-else PRESERVED
          if 'datetime' not in fields:
              fields = ['datetime'] + fields
  else:                               # <-- outer for-else LOST
      ...

Original:
  Inner FOR_ITER at 1548 -> 1624, JUMP_FORWARD 1644 -> 1798
Decompiled:
  Inner FOR_ITER at 1558 -> 1634, NO JUMP_FORWARD (else missing!)

Both inner and outer for-else are lost in decompilation.
"""
def nested_for_else(data, inner_check):
    outer_result = []
    for group in data:
        inner_result = []
        for item in group:
            if inner_check(item):
                return [item]
        if 'default' not in inner_result:
            inner_result.append('default')
        outer_result.extend(inner_result)
    else:
        outer_result.append('all_processed')
        return outer_result
code = nested_for_else.__code__
import dis
print('=== Nested for-else: inner preserved, outer lost ===')
dis.dis(code)
