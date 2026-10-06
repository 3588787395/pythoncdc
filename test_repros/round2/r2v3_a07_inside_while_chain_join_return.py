# round-2 r2v3 specimen (synthetic, minimal)
def f(q, stop):
    while not stop:
        flag = q.poll()
        if flag == 1:
            log('a')
        elif flag == -1:
            log('b')
        return q
        log('after')
