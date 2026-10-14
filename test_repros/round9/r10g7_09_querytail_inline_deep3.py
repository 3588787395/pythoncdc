def r10g7_09_querytail_inline_deep3(x, y, log):
    if x:
        if y:
            try:
                with CM(y):
                    d = g(y)
                if len(d) == 1:
                    return d[0]
                else:
                    return None
            except BaseException:
                log.error(d)
    return None
