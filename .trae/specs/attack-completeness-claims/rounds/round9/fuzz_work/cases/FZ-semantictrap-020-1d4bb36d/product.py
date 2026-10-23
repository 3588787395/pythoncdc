# Source Generated with Decompyle++ (Python version)
# File: subject.pyc (Python 3.11)

def main():
    events = []
    def gen(n):
        try:
            value = yield 0
            while value < n:
                yield value + 1
        finally:
            events.append('closed')
    g = gen(5)
    out = [next(g)]
    out.append(g.send(1))
    out.append(g.send(2))
    g.close()
    return (out, events)
