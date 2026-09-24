def f(recv, ev, q):
    try:
        info = recv()
        if info:
            q.put(info)
            ev.is_set() or ev.set()
    except Exception:
        pass
