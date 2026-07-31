# Pattern: dict subscript assignment chain (mirror read_model_file)
# Function: mirror zt_api.pyc read_model_file sequential dict build
# Expected: cfg = dict(); cfg['k1'] = float(m['a']); ...; return cfg
# Actual: same (pyc 100% match, NO-DEFECT control)
def build_cfg(model):
    cfg = dict()
    cfg['price'] = float(model['close'])
    cfg['price5'] = float(model['close_ma5'])
    cfg['ratio'] = float(model['change_ratio']) * 0.01
    cfg['days'] = int(model['turnover_days'])
    cfg['pct'] = float(cfg['price5'] / cfg['price'])
    return cfg
# NO-DEFECT
