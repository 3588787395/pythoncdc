def f(running, pre, upd):
    if pre:
        while running:
            if not upd:
                reset()
