def f(dt_strf):
    while True:
        if is_ft(dt_strf):
            sleep(3)
        elif dt_strf == '11:00:00':
            sleep(9)
        elif not (dt_strf > '15:15:00' or dt_strf < '08:30:00' or dt_strf == '12:00:00'):
            Q.put(dt_strf)
