# F-EXCTABLE/F-TERNARY (base.pyc SplitOrder.parse_time_info): if/else statement
# inside try leaves the branch jump outside the exception range (range splits
# with a gap); decompiler recovers a ternary whose jump stays inside (range
# contiguous) -> exception table differs, instructions identical.
def parse_time_info(time_info, log):
    if not time_info:
        s = 0
    elif isinstance(time_info, int):
        s = time_info
    else:
        try:
            h, ms = time_info.split('h', maxsplit=1)
            if h:
                h = int(h)
            else:
                h = 0
        except ValueError:
            log.error('x')
            h = 0
            ms = time_info
        try:
            m, s = ms.split('m', maxsplit=1)
            if m:
                m = int(m)
            else:
                m = 0
        except ValueError:
            log.error('x')
            m = 0
            s = ms
        if s.endswith('s'):
            s = s[:-1]
        s = int(s) if s else 0
        s = (h * 60 + m) * 60 + s
    if s <= 3:
        return 3
    else:
        return s
