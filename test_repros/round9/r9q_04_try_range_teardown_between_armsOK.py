# Source Generated with Decompyle++ (Python version)
# File: r9q_04_try_range_teardown_between_arms.pyc (Python 3.11)

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
