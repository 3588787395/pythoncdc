def f(recv, ev, q):
    try:
        info = recv()
        while info:
            q.put(info)
            r = ev.is_set() or ev.set()
            info = recv()
    except Exception:
        pass
