class Log(object):
    on = True

    def info(self, m):
        pass

    def dbg(self, m):
        pass


def w1(q, ev, log):
    while True:
        n = q.qsize()
        if n:
            buf = ''
            while n > 0:
                n -= 1
                x = q.get()
                if x:
                    log.dbg(x)
                else:
                    buf = f'{buf}{x}'
            if buf:
                log.info(buf)
        else:
            if log.on:
                ev.wait(1)
                continue
            else:
                break


def w2(q, ev, log):
    while True:
        n = q.qsize()
        if n:
            buf = ''
            while n > 0:
                n -= 1
                x = q.get()
                if x:
                    log.dbg(x)
                else:
                    buf = buf + x
            if buf:
                log.info(buf)
        else:
            if log.on:
                ev.wait(1)
                continue
            else:
                break


def w3(q, ev, log):
    while True:
        n = q.qsize()
        if n:
            buf = 0
            while n > 0:
                n -= 1
                x = q.get()
                buf += x
            if buf:
                log.info(buf)
            log.dbg(buf)
        else:
            if log.on:
                ev.wait(1)
                continue
            else:
                break
