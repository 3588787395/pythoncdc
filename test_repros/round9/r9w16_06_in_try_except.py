def r9w16_06_in_try_except(q, log):
    try:
        while True:
            if len(q) > 0:
                log(q[0])
            sleep(0.001)
    except ValueError:
        log('err')
