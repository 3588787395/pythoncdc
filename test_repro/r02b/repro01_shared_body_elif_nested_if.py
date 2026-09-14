def f(x):
    while True:
        try:
            if x == 1:
                print('a')
                time.sleep(3)
            elif not (x > 15 or x < 8):
                if 11 < x < 12:
                    time.sleep(60)
                elif 8 <= x < 9 or 12 <= x < 13:
                    time.sleep(60)
                elif 9 <= x < 10 or 13 <= x < 14:
                    time.sleep(0.5)
            elif x == 2:
                print('b')
            elif not (x > 14 or x < 9):
                pass
        except Exception:
            log.error('error')
            return None
