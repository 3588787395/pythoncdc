def r9w16_07_except_epilogue_join(q, log):
    while True:
        if len(q) > 0:
            try:
                x = q.pop(0)
                log(x)
            except ValueError:
                log('err')
        sleep(0.001)
