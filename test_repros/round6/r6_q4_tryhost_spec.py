def r6_q4_tryhost_spec(x):
    try:
        work(x)
    except OSError:
        log('e')
        return None
    finally:
        clean()
