def f(dt_strf, accounts):
    while True:
        try:
            if 'FUTURE' in accounts:
                if is_future(dt_strf):
                    enqueue(dt_strf)
                    sleep(3)
                elif not (dt_strf > '15:15' or dt_strf < '08:30'):
                    if '11:30' < dt_strf < '12:30':
                        sleep(60)
                    elif '08:30' <= dt_strf < '09:00':
                        sleep(60)
                    elif '09:00' <= dt_strf < '09:30' or '12:59' <= dt_strf < '13:00':
                        sleep(0.5)
            elif is_stock(dt_strf):
                enqueue(dt_strf)
                sleep(3)
            elif not (dt_strf > '15:00' or dt_strf < '09:00'):
                if '11:30' < dt_strf < '12:30':
                    sleep(60)
                elif '09:00' <= dt_strf < '09:30':
                    sleep(60)
                elif '09:29' <= dt_strf < '09:30':
                    sleep(0.5)
        except Exception:
            error('failed:{}'.format(msg()))
            return None
