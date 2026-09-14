"""Repro 5: for-else where else body replaces post-loop code

Original pattern from get_history_new:
  for stock in real_data_dict.keys():
      if len(his_data[stock]) == 0:
          kline_data_dict[stock] = real_data_dict[stock]
          continue
      kline_data_dict[stock] = np.concatenate(...)
  else:                                    # <-- else block
      kline_data_dict = real_data_dict     # <-- This is the else body

Original bytecode:
  1548 JUMP_FORWARD 64 (to 1678)          <-- else block start after for loop exhaustion
  1550 LOAD_FAST real_data_dict            <-- else body
  1552 STORE_FAST kline_data_dict          <-- else body
  1554 JUMP_FORWARD 61 (to 1678)          <-- else body end

Decompiled bytecode:
  1548 JUMP_FORWARD 2 (to 1554)           <-- else block WRONG SIZE (should be 64, got 2)
  1550 LOAD_FAST real_data_dict            <-- this looks like it runs unconditionally
  1552 STORE_FAST kline_data_dict
  1554 LOAD_FAST kline_data_dict
  1556 RETURN_VALUE                         <-- early return - skips rest of function!

The decompiler set the JUMP_FORWARD to only 2 bytes instead of 64,
causing the else block to appear as unconditional code and adding
an early return that skips the rest of the function.
"""
def for_else_early_return_wrong(data, extra):
    result = {}
    for key in data:
        if len(data[key]) == 0:
            result[key] = extra[key]
            continue
        result[key] = data[key] + extra[key]
    else:
        result = extra
    return result

code = for_else_early_return_wrong.__code__
import dis
print("=== for-else: JUMP_FORWARD wrong size causes early return ===")
dis.dis(code)
