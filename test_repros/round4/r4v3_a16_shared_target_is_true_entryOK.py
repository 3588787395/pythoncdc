# Source Generated with Decompyle++ (Python version)
# File: r4v3_a16_shared_target_is_true_entry.pyc (Python 3.11)

def f(rows, dt_strf):
    for row in rows:
        if dt_strf > '15:15:00' or dt_strf < '08:30:00':
            sleep(60)
        else:
            LOG.info(row)
            continue
