def r10g7_10_querytail_inline_double_pair(x, log):
    if x:
        try:
            d = g(x)
            if len(d) == 1:
                return d[0]
            else:
                return None
        except BaseException:
            log.error(d)
        while d:
            k(d)
    else:
        y = h(x)
    return None
