def r10g7_19_ctl_while_return_no_tail(running, items):
    while running:
        if items:
            return items[0]
        running = step(running)
    return None
