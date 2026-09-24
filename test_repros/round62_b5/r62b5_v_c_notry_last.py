def f(recv, ev, q):
    info = recv()
    while info:
        q.put(info)
        ev.is_set() or ev.set()
        info = recv()
