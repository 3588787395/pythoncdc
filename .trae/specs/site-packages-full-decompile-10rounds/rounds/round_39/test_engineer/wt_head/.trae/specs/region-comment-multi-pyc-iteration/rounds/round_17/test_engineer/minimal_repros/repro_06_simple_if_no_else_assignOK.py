# Source Generated with Decompyle++ (Python version)
# File: repro_06_simple_if_no_else_assign.pyc (Python 3.11)

def set_name(flag, info, cfg):
    if flag:
        cfg['factor_name'] = info[0]['factor_name']
    return cfg
