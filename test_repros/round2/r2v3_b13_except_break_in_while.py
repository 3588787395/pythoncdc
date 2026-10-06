# round-2 r2v3 specimen (synthetic, minimal)
def f(q, stop, w):
    while not stop:
        try:
            is_end, daily = q.get(timeout=1)
        except ValueError:
            break
        w(is_end, daily)
    return None
