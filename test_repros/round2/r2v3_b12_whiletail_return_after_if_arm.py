# round-2 r2v3 specimen (synthetic, minimal)
def f(stop, TH):
    while not stop:
        from mod import THREAD_STATUS
        if THREAD_STATUS:
            return None
        time.sleep(0.01)
    return None
