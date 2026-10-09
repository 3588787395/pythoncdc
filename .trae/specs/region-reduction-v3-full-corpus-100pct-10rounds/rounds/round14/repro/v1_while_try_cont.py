import time

def f(self, dt_strf):
    while True:
        try:
            if dt_strf > '15:15:00' or dt_strf < '08:30:00' or '11:30:00' < dt_strf < '12:30:00':
                time.sleep(60)
                continue
            elif '08:30:00' <= dt_strf < '08:59:00':
                time.sleep(30)
                continue
            break
        except Exception:
            pass
