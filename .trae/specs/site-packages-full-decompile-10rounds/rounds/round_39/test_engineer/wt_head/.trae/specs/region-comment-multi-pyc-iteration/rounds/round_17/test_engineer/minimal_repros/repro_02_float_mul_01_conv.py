# Pattern: float(x) * 0.01 conversion assignment (mirror read_model_file change_percent)
# Function: mirror zt_api.pyc read_model_file * 0.01 conversions
# Expected: a = float(m['x']) * 0.01; b = float(m['y']) * 0.01
# Actual: same (pyc 100% match, NO-DEFECT control)
def conv_pct(model):
    a = float(model['change_ratio']) * 0.01
    b = float(model['change_ratio_high']) * 0.01
    c = float(model['change_ratio_low']) * 0.01
    return a + b + c
# NO-DEFECT
