# round-2 r2v3 specimen (synthetic, minimal)
def f(TH):
    while True:
        if TH:
            break
        time.sleep(0.01)
    event_bus = get_bus()
