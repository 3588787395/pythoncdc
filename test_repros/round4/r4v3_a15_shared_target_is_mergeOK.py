# Source Generated with Decompyle++ (Python version)
# File: r4v3_a15_shared_target_is_merge.pyc (Python 3.11)

def f(rows, dt_strf):
    for row in rows:
        if is_ft(dt_strf):
            Q.put(row)
            continue
        elif not (dt_strf > '15:15:00' or dt_strf < '08:30:00'):
            if dt_strf == '12:00:00':
                sleep(60)
                continue
            sleep(1)
