def f(x):
    while True:
        try:
            if x == 1:
                do_a()
            elif not (x > 10 or x < 5):
                if 7 < x < 8:
                    do_shared()
                elif 5 <= x < 6:
                    do_b()
            elif x == 2:
                do_c()
        except Exception:
            return None
