# Source Generated with Decompyle++ (Python version)
# File: r9q_23_for_try_while_nested_dump.pyc (Python 3.11)

def try_wraps_while_dump(lg, sock, dq):
    for rnd in range(3):
        try:
            while True:
                try:
                    m = sock.recv()
                except BaseException as x:
                    lg.error(str(x))
                if m:
                    dq.append(m)
                else:
                    lg.warn('empty')
        except BaseException as ex:
            lg.error(str(ex))
