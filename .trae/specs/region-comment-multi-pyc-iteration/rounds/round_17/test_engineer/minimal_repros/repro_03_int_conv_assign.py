# Pattern: int(x) conversion assignment (mirror read_model_file stock_avg_poly)
# Function: mirror zt_api.pyc read_model_file int() conversions
# Expected: cfg['poly1'] = int(model['indiv_ma5_up']); ...
# Actual: same (pyc 100% match, NO-DEFECT control)
def conv_int(model):
    cfg = dict()
    cfg['poly1'] = int(model['indiv_ma5_up'])
    cfg['poly2'] = int(model['indiv_ma10_up'])
    cfg['poly3'] = int(model['indiv_ma20_up'])
    return cfg
# NO-DEFECT
