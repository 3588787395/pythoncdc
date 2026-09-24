FLAG = '1'


def setup(handlers, engine):
    second = builder(int(engine.a) if FLAG == '1' else 2, engine.c, encoding='UTF-8')
    second = wrap_async(second)
    for h in (handlers.x, handlers.y):
        h.add_handler(second)
    return second
