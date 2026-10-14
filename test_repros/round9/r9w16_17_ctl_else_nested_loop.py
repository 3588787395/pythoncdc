def r9w16_17_ctl_else_nested_loop(n, q, log):
    while n > 0:
        n = n - 1
    else:
        while q:
            log(q.pop(0))
