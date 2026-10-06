# round-2 r2v3 specimen (synthetic, minimal)
def f(is_end, TH):
    if is_end:
        while True:
            if TH:
                return 1
            time.sleep(0.01)
    event_bus = get_bus()
