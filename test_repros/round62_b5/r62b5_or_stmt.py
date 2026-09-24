def or_stmt_in_loop(recv, ev, q):
    info = recv()
    while info:
        q.put(info)
        ev.is_set() or ev.set()
        info = recv()
