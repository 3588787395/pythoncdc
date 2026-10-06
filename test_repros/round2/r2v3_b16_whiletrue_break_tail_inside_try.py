# round-2 r2v3 specimen (synthetic, minimal)
def f(is_end, TH):
    try:
        while True:
            if TH:
                break
            time.sleep(0.01)
    except ValueError:
        log('e')
    event_bus = get_bus()
