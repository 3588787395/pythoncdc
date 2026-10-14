def f(dt_strf):
    if dt_strf > '15:15:00' or dt_strf < '08:30:00' or '11:30:00' < dt_strf < '12:30:00':
        return 1
    elif dt_strf == 'x':
        return 2
    return 3
