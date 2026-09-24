FLAG = '1'


def setup(handlers, engine):
    second = builder(engine.c, kw=int(engine.a) if FLAG == '1' else 2)
    second = wrap_async(second)
    for h in (handlers.x, handlers.y):
        h.add_handler(second)
    for h2 in (handlers.x, handlers.z):
        h2.add_handler(second)
