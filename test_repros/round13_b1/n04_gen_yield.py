def gen(seq):
    yield 1
    yield from seq
    x = yield 2
    for s in seq:
        yield s
