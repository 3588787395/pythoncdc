# F-EXCTABLE (base.SplitOrder.parse_time_info): instruction sequences are byte-equal
# but the emitted exception-table ranges differ (ETDIFF 6/6, d1=4/4) because the
# second try's range starts one instruction late/early.
def parse_time_info(s):
    try:
        t = str(s)
        return int(t)
    except ValueError:
        t = None
    try:
        return len(t)
    except TypeError:
        return -1
