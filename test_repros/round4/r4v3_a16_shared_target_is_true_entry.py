def f(rows, dt_strf):
    for row in rows:
        if dt_strf > '15:15:00' or dt_strf < '08:30:00':
            sleep(60)
        else:
            LOG.info(row)
