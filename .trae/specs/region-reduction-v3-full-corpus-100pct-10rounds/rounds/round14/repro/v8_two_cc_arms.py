import time

def f(self, dt_strf, accounts):
    while True:
        try:
            if 'FUTURE' in accounts:
                if self.is_future(dt_strf):
                    time.sleep(3)
                    continue
                elif dt_strf > '15:15:00' or dt_strf < '08:30:00' or '11:30:00' < dt_strf < '12:30:00':
                    time.sleep(60)
                    continue
                elif '08:30:00' <= dt_strf < '08:59:00' or '12:30:00' <= dt_strf < '12:59:00':
                    time.sleep(60)
                    continue
            elif dt_strf > '15:00:00' or dt_strf < '09:00:00' or '11:30:00' < dt_strf < '12:30:00':
                time.sleep(60)
                continue
            elif '09:00:00' <= dt_strf < '09:29:00' or '12:30:00' <= dt_strf < '12:59:00':
                time.sleep(60)
                continue
            break
        except Exception:
            pass
