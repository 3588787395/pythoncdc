def two_try_shared_handler(sock, lg, lk):
    message = sock.recv()
    try:
        data = eval(message)
    except BaseException as x:
        lg.error(str(x))
        lk.acquire()
        return None
    process(data)
    try:
        send(data)
    except Timeout:
        lg.error('timeout')
    lk.release()
