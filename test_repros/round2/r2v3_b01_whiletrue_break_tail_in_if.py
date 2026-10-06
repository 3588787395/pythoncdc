# round-2 r2v3 specimen (synthetic, minimal)
def f(is_end, TH):
    if is_end:
        while True:
            from mod import THREAD_STATUS
            if THREAD_STATUS:
                break
            time.sleep(0.01)
    event_bus = get_bus()
    event_bus.publish()
