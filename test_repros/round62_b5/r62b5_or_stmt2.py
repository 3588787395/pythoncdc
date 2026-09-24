def or_stmt_in_try(recv, ev, q, t):
    try:
        info = recv()
        while info:
            q.put(info)
            ev.is_set() or ev.set()
            info = recv()
    except BaseException as e:
        if q.qsize():
            t.join()
        if not isinstance(e, EOFError):
            raise
