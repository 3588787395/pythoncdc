def main():
    events = []
    def gen(n):
        try:
            value = yield 0
            while value < n:
                value = yield value + 1
        finally:
            events.append("closed")
    g = gen(5)
    out = [next(g)]
    out.append(g.send(1))
    out.append(g.send(2))
    return out, events
