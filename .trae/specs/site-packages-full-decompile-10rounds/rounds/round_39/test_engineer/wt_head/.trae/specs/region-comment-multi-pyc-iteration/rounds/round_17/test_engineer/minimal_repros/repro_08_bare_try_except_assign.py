# Pattern: bare try/except with assignment in except (mirror read_config_file hold_days)
# Function: mirror zt_api.pyc read_config_file hold_days try/except
# Expected: try: cfg['hold_days'] = int(info[0]['hold_days']) except: cfg['hold_days'] = 10
# Actual: same (pyc 100% match, NO-DEFECT control)
def hold(info, cfg):
    try:
        cfg['hold_days'] = int(info[0]['hold_days'])
    except:
        cfg['hold_days'] = 10
    return cfg
# NO-DEFECT
