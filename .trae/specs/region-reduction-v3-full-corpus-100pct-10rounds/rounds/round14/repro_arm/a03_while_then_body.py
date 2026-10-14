def f(self, dt):
    while self.running:
        if dt > 'a' or 'b' < dt < 'c':
            dt = 'x'
            continue
        dt = 'y'
    return None
