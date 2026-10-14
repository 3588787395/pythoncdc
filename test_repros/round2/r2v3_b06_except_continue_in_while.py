# round-2 r2v3 specimen (synthetic, minimal)
def f(q, stop, w):
    while not stop:
        try:
            is_end, daily = q.get(timeout=1)
        except ValueError:
            continue
        w(is_end, daily)
        if is_end:
            break
    while not stop:
        if stop.flag:
            return None
        time.sleep(0.01)
