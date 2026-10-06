# Source Generated with Decompyle++ (Python version)
# File: r4v3_a01_corpus_tick_elifchain.pyc (Python 3.11)

def f(dt_strf):
    while True:
        try:
            if 'x' in ACCTS:
                if is_ft(dt_strf):
                    Q.put(dt_strf)
                    sleep(3)
                elif not (dt_strf > '15:15:00' or dt_strf < '08:30:00'):
                    if '11:30:00' < dt_strf < '12:30:00':
                        sleep(60)
                    elif '08:30:00' <= dt_strf < '08:59:00' or '12:30:00' <= dt_strf < '12:59:00':
                        sleep(60)
                    elif '08:59:00' <= dt_strf < '09:00:00' or '12:59:00' <= dt_strf < '13:00:00':
                        sleep(1)
        except Exception:
            LOG.error('boom')
            return None
