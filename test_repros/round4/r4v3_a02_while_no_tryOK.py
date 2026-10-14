# Source Generated with Decompyle++ (Python version)
# File: r4v3_a02_while_no_try.pyc (Python 3.11)

def f(dt_strf):
    while 'x' in ACCTS:
        if is_ft(dt_strf):
            Q.put(dt_strf)
            sleep(3)
        elif not (dt_strf > '15:15:00' or dt_strf < '08:30:00'):
            if '11:30:00' < dt_strf < '12:30:00':
                break
            elif '08:30:00' <= dt_strf < '08:59:00' or '12:30:00' <= dt_strf:
                if '12:59:00':
                    break
                elif '08:59:00' <= dt_strf:
                    if '09:00:00':
                        pass
                    else:
                        sleep(1)
                if '12:59:00' <= dt_strf < '13:00:00':
                    pass
            elif '12:30:00' <= dt_strf < '12:59:00':
                pass
            elif '08:59:00' <= dt_strf < '09:00:00' or '12:59:00' <= dt_strf:
                pass
    sleep(60)
    sleep(60)
