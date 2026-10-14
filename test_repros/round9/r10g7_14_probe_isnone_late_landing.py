def r10g7_14_probe_isnone_late_landing(t, a, b, log):
    if t == 'short_status':
        if a is None or b is None:
            return
        for i in a:
            log(i)
        return down(a[-1], b[-1])
    return None
