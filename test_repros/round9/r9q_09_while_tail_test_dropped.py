def loop_tail_test(sub, sock, lg):
    while sub.isSet():
        try:
            m = sock.recv()
            if m:
                lg.info(m)
            else:
                lg.warn('empty')
        except BaseException as ex:
            lg.error(str(ex))
        sub.isSet()
