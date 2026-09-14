def f(dt_strf):
    while True:
        try:
            if AccountType.FUTURE.value in accounts:
                if is_future_tradetime(dt_strf):
                    queue.put((dt_strf, 'TICK'))
                    time.sleep(3)
                elif not (dt_strf > '15:15:00' or dt_strf < '08:30:00'):
                    if '11:30:00' < dt_strf < '12:30:00':
                        time.sleep(60)
                    elif '08:30:00' <= dt_strf < '08:59:00' or '12:30:00' <= dt_strf < '12:59:00':
                        time.sleep(60)
                    elif '08:59:00' <= dt_strf < '09:00:00' or '12:59:00' <= dt_strf < '13:00:00':
                        time.sleep(0.5)
                elif is_stock_tradetime(dt_strf):
                    queue.put((dt_strf, 'TICK'))
                    time.sleep(3)
                elif not (dt_strf > '15:00:00' or dt_strf < '09:00:00'):
                    if '11:30:00' < dt_strf < '12:30:00':
                        time.sleep(60)
                    elif '09:00:00' <= dt_strf < '09:29:00' or '12:30:00' <= dt_strf < '12:59:00':
                        time.sleep(60)
                    elif '09:29:00' <= dt_strf < '09:30:00' or '12:59:00' <= dt_strf < '13:00:00':
                        time.sleep(0.5)
        except Exception:
            log.error('err:{}'.format(get_msg()))
            return None
