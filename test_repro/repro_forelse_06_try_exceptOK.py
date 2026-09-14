# Source Generated with Decompyle++ (Python version)
# File: repro_forelse_06_try_except.pyc (Python 3.11)

__doc__ = """Repro 6: for-else inside try-except - else block absorbed by except handler

Original pattern from get_trade_unit_info:
  try:
      for line in csv_reader:
          if line[2] == '0' or line[2] == '3':
              tempBacktestIds.append(line[0])
      else:                                    # <-- for-else inside try
          # process tempBacktestIds
          pass
  except BaseException:
      app_log.info('read file failed')

Original bytecode:
  FOR_ITER at 410 -> target 518
  JUMP_FORWARD at 518 -> 632 (else block, jumps past except handler)

Decompiled bytecode:
  FOR_ITER at 410 -> target 518
  JUMP_FORWARD at 518 -> 632 (else block preserved)

BUT the second for-else:
Original:
  FOR_ITER at 908 -> target 1186
  JUMP_FORWARD at 1186 -> 1296 (else block)

Decompiled:
  FOR_ITER at 904 -> target 1182
  No JUMP_FORWARD! (else block missing)
  At 1182: fp.close() code runs unconditionally instead of in else

The else block is merged into the post-loop code within the try block.
"""
def for_else_in_try_except(data, key):
    result = []
    try:
        for item in data:
            if item == key:
                result.append(item)
        else:
            result.append('processed_all')
    except Exception:
        result.append('error')
    return result
code = for_else_in_try_except.__code__
import dis
print('=== for-else inside try-except: else absorbed by except handler ===')
dis.dis(code)
