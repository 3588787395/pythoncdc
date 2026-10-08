# Source Generated with Decompyle++ (Python version)
# File: r10g7_14_probe_isnone_late_landing.pyc (Python 3.11)

def r10g7_14_probe_isnone_late_landing(t, a, b, log):
    if t == 'short_status':
        if not a is not None or b is None:
            return None
        else:
            for i in a:
                log(i)
            return down(a[-1], b[-1])
    else:
        return None
