def f(x):
    while True:
        try:
            if x > 100:
                time.sleep(3)
            elif not (x > 50 or x < 10):
                if 30 < x < 40:
                    time.sleep(60)
                elif 10 <= x < 20 or 40 <= x < 50:
                    time.sleep(60)
                elif 20 <= x < 25:
                    time.sleep(0.5)
            elif x > 0:
                time.sleep(3)
            elif not (x > 40 or x < 15):
                if 25 < x < 30:
                    time.sleep(60)
                elif 15 <= x < 20:
                    time.sleep(60)
                elif 20 <= x < 22 or 35 <= x < 38:
                    time.sleep(0.5)
        except Exception:
            log.error('err')
            return None
