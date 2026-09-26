# F-FORITER/F-TERNARY (wizard_quant_api get_DMI.calculate_di genexpr x2): ternary
# inside a genexpr -- orig FOR_ITER exit lands on a block chain holding the
# ternary's `else 0` const block; decompiler drops/merges it.
def calculate_di(high, low, pre_close, n1):
    high_now = high[1:]
    low_now = low[1:]
    tr = sum((max(max(high_now[i] - low_now[i], abs(high_now[i] - pre_close[i])), abs(low_now[i] - pre_close[i])) for i in range(n1)))
    dmp = sum((high[-i] - high[-(i + 1)] if high[-i] - high[-(i + 1)] > low[-(i + 1)] - low[-i] else 0 for i in range(1, n1 + 1)))
    dmm = sum((low[-(i + 1)] - low[-i] if low[-(i + 1)] - low[-i] > high[-i] - high[-(i + 1)] else 0 for i in range(1, n1 + 1)))
    di1 = dmp * 100 / tr
    di2 = dmm * 100 / tr
    return (di1, di2)
