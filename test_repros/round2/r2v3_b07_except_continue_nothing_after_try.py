# round-2 r2v3 specimen (synthetic, minimal)
def f(q, stop):
    while not stop:
        try:
            is_end, daily = q.get(timeout=1)
        except ValueError:
            continue
        w(daily)
