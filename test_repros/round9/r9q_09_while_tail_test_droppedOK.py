# Source Generated with Decompyle++ (Python version)
# File: r9q_09_while_tail_test_dropped.pyc (Python 3.11)

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
