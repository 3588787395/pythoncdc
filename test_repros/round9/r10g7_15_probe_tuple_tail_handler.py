def r10g7_15_probe_tuple_tail_handler(x, flag, log):
    if x:
        try:
            a = g(x)
        except BaseException:
            log.error(a)
            while flag:
                log(flag)
            return None, flag
    b = h(a)
    return b
