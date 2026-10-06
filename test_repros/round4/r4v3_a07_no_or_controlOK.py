# Source Generated with Decompyle++ (Python version)
# File: r4v3_a07_no_or_control.pyc (Python 3.11)

def f(dt_strf):
    while 'x' in ACCTS:
        if is_ft(dt_strf):
            Q.put(dt_strf)
            sleep(3)
        elif dt_strf > '15:15:00' or dt_strf < '08:30:00':
            if '11:30:00' < dt_strf < '12:30:00':
                break
            elif '08:30:00' <= dt_strf < '08:59:00':
                break
            elif '08:59:00' <= dt_strf < '09:00:00':
                sleep(1)
    sleep(60)
    sleep(60)
