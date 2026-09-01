# Pattern: float(a / b) division-then-float (mirror read_model_file close_percent)
# Function: mirror zt_api.pyc read_model_file close_percentN expressions
# Expected: float(cfg['price5'] / cfg['price'])
# Actual: same (pyc 100% match, NO-DEFECT control)
def close_percent(price5, price10, price):
    p1 = float(price5 / price)
    p2 = float(price10 / price)
    return p1 + p2
# NO-DEFECT
