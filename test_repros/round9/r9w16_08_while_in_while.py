def r9w16_08_while_in_while(flag, q, log):
    while flag:
        while True:
            if len(q) > 0:
                log(q[0])
            sleep(0.001)
        flag = 0
