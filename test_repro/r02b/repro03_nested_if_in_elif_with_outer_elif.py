def f(x):
    while True:
        try:
            if cond_a(x):
                action_a()
            elif not (x > 15 or x < 8):
                if 11 < x < 12:
                    time.sleep(60)
                elif 8 <= x < 9 or 12 <= x < 13:
                    time.sleep(60)
            elif cond_b(x):
                action_b()
        except Exception:
            log.error('err')
