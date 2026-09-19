"""Repro: kill_trade_process nested-if flattening (semantic change).

Original shape:
    if os.path.getsize(path) == 0:
        log('empty')
        os.system('rm ...')
        if len(id_list) > 0:
            return True
    return False

The decompiler flattens this to:
    log('empty')
    os.system('rm ...')
    if os.path.getsize(path) == 0 and len(id_list) > 0:
        return True
i.e. it hoists the outer if-body statements above the condition and
merges the two ifs into one `and` condition. The statements now run
unconditionally -- bytecode layout shifts and the side effects change.
"""
import os

_app_log = print


def kill(path, id_list):
    try:
        _app_log('killing')
        os.system('kill %d' % 1)
        if os.path.getsize(path) == 0:
            _app_log('empty file')
            os.system('rm -rf {}'.format(path))
            if len(id_list) > 0:
                _app_log('regen {}'.format(id_list))
                now = (2024, 1, 1)
                return True
    except BaseException:
        _app_log('kill failed')
    return False
