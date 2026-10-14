def while_try_dump(sub, sock, dq, lg):
    while sub.isSet():
        try:
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
        sub.isSet()
