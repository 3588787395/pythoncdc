# Source Generated with Decompyle++ (Python version)
# File: r9q_17_continue_through_handler.pyc (Python 3.11)

def continue_through_handler(sock, dq, lg):
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
        process(m)
