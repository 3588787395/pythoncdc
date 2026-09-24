FLAG = '1'


def setup(handlers, engine):
    second = builder(engine.c, encoding='UTF-8')
    second = wrap_async(second)
    for h in (handlers.x, handlers.y):
        h.add_handler(second)
