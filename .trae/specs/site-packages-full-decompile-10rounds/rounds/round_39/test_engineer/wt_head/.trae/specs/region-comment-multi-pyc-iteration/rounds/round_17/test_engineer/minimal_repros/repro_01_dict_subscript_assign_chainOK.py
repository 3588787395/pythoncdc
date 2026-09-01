# Source Generated with Decompyle++ (Python version)
# File: repro_01_dict_subscript_assign_chain.pyc (Python 3.11)

def build_cfg(model):
    cfg = dict()
    cfg['price'] = float(model['close'])
    cfg['price5'] = float(model['close_ma5'])
    cfg['ratio'] = float(model['change_ratio']) * 0.01
    cfg['days'] = int(model['turnover_days'])
    cfg['pct'] = float(cfg['price5'] / cfg['price'])
    return cfg
