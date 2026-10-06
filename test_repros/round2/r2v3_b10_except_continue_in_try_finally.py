# round-2 r2v3 specimen (synthetic, minimal)
def f(q, stop, w):
    while not stop:
        try:
            try:
                is_end, daily = q.get(timeout=1)
            except ValueError:
                continue
            w(is_end, daily)
        finally:
            log('fin')
