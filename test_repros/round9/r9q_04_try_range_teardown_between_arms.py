def tick(sock, dq, lg):
    while True:
        try:
            message = sock.recv()
        except Again:
            continue
        if message:
            try:
                dq.append(eval(message))
            except BaseException as x:
                lg.error(str(x))
        else:
            lg.warn('empty')
        sleep(0)
