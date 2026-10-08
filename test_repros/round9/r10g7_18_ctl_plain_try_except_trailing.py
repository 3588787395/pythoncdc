def r10g7_18_ctl_plain_try_except_trailing(x, log):
    try:
        a = g(x)
    except BaseException:
        log.error(a)
    b = finalize(a)
    return b
