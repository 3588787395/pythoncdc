# round-2 r2v3 specimen (synthetic, minimal)
def f(is_end, TH):
    if is_end:
        while True:
            if TH:
                break
    event_bus = get_bus()
    event_bus.publish()
