def f(x):
    while True:
        try:
            if x == 1:
                time.sleep(3)
            elif not (x > 15 or x < 8):
                if 11 < x < 12:
                    time.sleep(60)
                elif 8 <= x < 9:
                    time.sleep(60)
            elif x == 2:
                time.sleep(3)
        except Exception:
            return None
