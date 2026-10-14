def r9w16_16_ctl_plain_while_tail(x, log):
    while x > 0:
        x = x - 1
        log(x)
    return x
