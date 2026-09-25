# -*- coding: utf-8 -*-
def probe(src, is_async, func, is_dict):
    try:
        if is_async:
            if func:
                return src, ({} if is_dict else [])
            return {'error_no': -1, 'error_info': 'm'}, ({} if is_dict else [])
        return 0
    except Exception:
        return None
