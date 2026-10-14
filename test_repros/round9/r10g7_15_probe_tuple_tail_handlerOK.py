# Source Generated with Decompyle++ (Python version)
# File: r10g7_15_probe_tuple_tail_handler.pyc (Python 3.11)

def r10g7_15_probe_tuple_tail_handler(x, flag, log):
    if x:
        try:
            a = g(x)
        except BaseException:
            log.error(a)
            while flag:
                log(flag)
            return (None, flag)
    b = h(a)
    return b
