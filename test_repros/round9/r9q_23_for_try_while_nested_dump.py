def try_wraps_while_dump(lg, sock, dq):
    for rnd in range(3):
        try:
            while True:
                try:
                    m = sock.recv()
                except BaseException as x:
                    lg.error(str(x))
                    continue
                if m:
                    dq.append(m)
                else:
                    lg.warn('empty')
        except BaseException as ex:
            lg.error(str(ex))
