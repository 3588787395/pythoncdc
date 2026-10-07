def f(rows, dt_strf):
    for row in rows:
        if is_ft(dt_strf):
            Q.put(row)
        elif not (dt_strf > '15:15:00' or dt_strf < '08:30:00'):
            if dt_strf == '12:00:00':
                sleep(60)
            else:
                sleep(1)
