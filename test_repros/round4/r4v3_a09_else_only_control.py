def f(dt_strf):
    while True:
        if 'x' in ACCTS:
            if is_ft(dt_strf):
                Q.put(dt_strf)
                sleep(3)
            elif not (dt_strf > '15:15:00' or dt_strf < '08:30:00'):
                if '11:30:00' < dt_strf < '12:30:00':
                    sleep(60)
                else:
                    sleep(1)
