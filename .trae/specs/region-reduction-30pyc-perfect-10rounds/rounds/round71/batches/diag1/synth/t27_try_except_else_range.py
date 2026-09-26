# F-EXCTABLE (base.SplitOrder.parse_time_info): `try/except/else` -- the else-clause
# must stay outside the protected range (A: 66..118 / 264..316). Decompiler folds the
# else into the try body (B: 66..156 / 264..354) so the exception-table ranges shift
# while every instruction stays byte-identical (144/144).
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
    return s
