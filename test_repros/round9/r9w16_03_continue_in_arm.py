def r9w16_03_continue_in_arm(q, log):
    while True:
        if len(q) > 0:
            x = q.pop(0)
            if x.skip:
                continue
            log(x)
        sleep(0.001)
