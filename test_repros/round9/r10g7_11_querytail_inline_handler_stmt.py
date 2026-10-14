def r10g7_11_querytail_inline_handler_stmt(x, log):
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
            time.sleep(1)
    return None
