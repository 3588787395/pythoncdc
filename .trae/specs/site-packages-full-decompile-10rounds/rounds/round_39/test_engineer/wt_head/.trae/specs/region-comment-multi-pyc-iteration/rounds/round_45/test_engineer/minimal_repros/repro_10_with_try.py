
def func(lock):
    with lock:
        try:
            return 1
        except Exception:
            return 0
