# Pattern: simple if (no else) with body assignment (mirror read_config_file is_trade_flag)
# Function: mirror zt_api.pyc read_config_file is_trade_flag branch
# Expected: if flag: cfg['factor_name'] = info[0]['factor_name']
# Actual: same (pyc 100% match, NO-DEFECT control)
def set_name(flag, info, cfg):
    if flag:
        cfg['factor_name'] = info[0]['factor_name']
    return cfg
# NO-DEFECT
