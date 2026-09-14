def f(x):
    while True:
        try:
            if x == 'A':
                handle_a()
            elif not (x > 'Z' or x < 'A'):
                if 'L' < x < 'M':
                    wait()
                elif 'A' <= x < 'C' or 'M' <= x < 'O':
                    wait()
            elif x == 'B':
                handle_b()
        except Exception:
            return None
