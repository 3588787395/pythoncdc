if 'x' in ACCTS:
    if is_ft(DT):
        Q.put(DT)
        sleep(3)
    elif not (DT > '15:15:00' or DT < '08:30:00'):
        if '11:30:00' < DT < '12:30:00':
            sleep(60)
        elif '08:30:00' <= DT < '08:59:00' or '12:30:00' <= DT < '12:59:00':
            sleep(60)
        elif '08:59:00' <= DT < '09:00:00' or '12:59:00' <= DT < '13:00:00':
            sleep(1)
