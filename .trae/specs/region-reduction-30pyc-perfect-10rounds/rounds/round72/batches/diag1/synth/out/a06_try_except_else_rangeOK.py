# Source Generated with Decompyle++ (Python version)
# File: a06_try_except_else_range.pyc (Python 3.11)

def parse_time_info(time_info):
    if not time_info:
        s = 0
    elif isinstance(time_info, int):
        s = time_info
    else:
        try:
            h, ms = time_info.split('h', maxsplit=1)
        except ValueError:
            h = 0
            ms = time_info
        else:
            h = int(h) if h else 0
        try:
            m, s = ms.split('m', maxsplit=1)
        except ValueError:
            m = 0
            s = ms
        else:
            m = int(m) if m else 0
        if s.endswith('s'):
            s = s[:-1]
        s = int(s) if s else 0
        s = (h * 60 + m) * 60 + s
    if s <= 3:
        return 3
    else:
        return s
