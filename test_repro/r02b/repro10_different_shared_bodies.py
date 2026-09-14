def f(x):
    while True:
        try:
            if x > 100:
                do_fast()
            elif not (x > 50 or x < 10):
                if 30 < x < 35:
                    do_slow()
                elif 10 <= x < 20:
                    do_medium()
                elif 20 <= x < 25:
                    do_fast()
            elif x > 0:
                do_other()
            elif not (x > 45 or x < 15):
                if 25 < x < 30:
                    do_slow()
                elif 15 <= x < 20:
                    do_medium()
                elif 20 <= x < 22:
                    do_fast()
        except Exception:
            log.error('error:{}'.format(str(e)))
            return None
