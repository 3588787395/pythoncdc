def f(x):
    while True:
        try:
            if x == 1:
                time.sleep(3)
            elif not (x > 20 or x < 5):
                if 12 < x < 15:
                    time.sleep(60)
                elif 5 <= x < 8:
                    time.sleep(60)
                elif 8 <= x < 10:
                    time.sleep(0.5)
            elif check_stock(x):
                time.sleep(3)
            elif not (x > 18 or x < 6):
                if 10 < x < 12:
                    time.sleep(60)
                elif 6 <= x < 8:
                    time.sleep(60)
                elif 8 <= x < 9 or 16 <= x < 17:
                    time.sleep(0.5)
        except Exception:
            log.error('err')
            return None
