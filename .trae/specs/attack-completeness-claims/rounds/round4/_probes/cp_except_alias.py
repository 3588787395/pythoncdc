class MyErr(Exception):
    pass
def f():
    try:
        raise MyErr()
    except MyErr:
        return 1
