def r9w16_02_break_in_arm(q, log):
    while True:
        if len(q) > 0:
            x = q.pop(0)
            if x.done:
                break
            log(x)
        sleep(0.001)
