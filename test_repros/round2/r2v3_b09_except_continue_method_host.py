# round-2 r2v3 specimen (synthetic, minimal)
class C:
    def m(self, q, stop, w):
        while not stop:
            try:
                is_end, daily = q.get(timeout=1)
            except ValueError:
                continue
            w(is_end, daily)
            if is_end:
                break
        return None
