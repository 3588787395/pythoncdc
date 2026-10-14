import time

def f(self, dt_strf):
    try:
        if dt_strf > '15:15:00' or dt_strf < '08:30:00' or '11:30:00' < dt_strf < '12:30:00':
            time.sleep(60)
            return 1
        elif '08:30:00' <= dt_strf < '08:59:00':
            time.sleep(30)
            return 2
        return 3
    except Exception:
        pass
