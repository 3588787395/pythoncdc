def r6_q4_tryhost_ctl(x):
    try:
        work(x)
    except OSError:
        log('e')
    finally:
        clean()
