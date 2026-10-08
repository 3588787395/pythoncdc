def r10g7_06_loopexit_pair_handler_then_loop(x, log, running):
    if x:
        try:
            with CM(x):
                d = g(x)
        except BaseException:
            log.error(d)
        while running:
            k(d)
    else:
        y = h()
