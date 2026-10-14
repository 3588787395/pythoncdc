# round-2 r2v3 specimen (synthetic, minimal)
def f(is_end, TH, stop):
    if is_end:
        while not stop:
            if TH:
                break
            time.sleep(0.01)
    event_bus = get_bus()
    event_bus.publish()
