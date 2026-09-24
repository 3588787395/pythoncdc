def f(recv, ev, q):
    try:
        info = recv()
        while info:
            q.put(info)
            info = recv()
            ev.is_set() or ev.set()
    except Exception:
        pass
