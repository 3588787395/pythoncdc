# Source Generated with Decompyle++ (Python version)
# File: repro_08_bare_try_except_assign.pyc (Python 3.11)

def hold(info, cfg):
    try:
        cfg['hold_days'] = int(info[0]['hold_days'])
    except:
        cfg['hold_days'] = 10
    return cfg
