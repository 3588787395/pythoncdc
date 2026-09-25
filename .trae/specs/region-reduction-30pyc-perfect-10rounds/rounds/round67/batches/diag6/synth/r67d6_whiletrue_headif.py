def w1(q_source, st, printer):
    while True:
        q = q_source.qsize()
        if q:
            msgs = ''
            while q > 0:
                q -= 1
                msgs = msgs + 'x'
            if msgs:
                printer(msgs)
        else:
            if st:
                continue
            else:
                break
