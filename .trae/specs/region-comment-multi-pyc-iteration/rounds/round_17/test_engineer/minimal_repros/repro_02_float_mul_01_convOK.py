# Source Generated with Decompyle++ (Python version)
# File: repro_02_float_mul_01_conv.pyc (Python 3.11)

def conv_pct(model):
    a = float(model['change_ratio']) * 0.01
    b = float(model['change_ratio_high']) * 0.01
    c = float(model['change_ratio_low']) * 0.01
    return a + b + c
