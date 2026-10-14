def r10g7_07_querytail_inline_single(x, log):
    if x:
        try:
            with CM(x):
                d = g(x)
            if len(d) == 1:
                return d[0]
            else:
                return None
        except BaseException:
            log.error(d)
    return None
