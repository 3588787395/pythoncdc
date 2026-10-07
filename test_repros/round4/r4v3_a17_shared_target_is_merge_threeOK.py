# Source Generated with Decompyle++ (Python version)
# File: r4v3_a17_shared_target_is_merge_three.pyc (Python 3.11)

def f(dt_strf):
    while True:
        if is_ft(dt_strf):
            sleep(3)
        elif dt_strf == '11:00:00':
            sleep(9)
        elif not (dt_strf > '15:15:00' or dt_strf < '08:30:00' or dt_strf == '12:00:00'):
            Q.put(dt_strf)
