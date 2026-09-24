FLAG = '1'


def setup(handlers, engine):
    first = builder(int(engine.a) if FLAG == '1' else 2, engine.b, encoding='UTF-8')
    second = builder(int(engine.a) if FLAG == '1' else 2, engine.c, encoding='UTF-8')
    first = wrap_async(first)
    note_only(second)
    second = wrap_async(second)
    for h in (handlers.x, handlers.y):
        h.add_handler(first)
    for h2 in (handlers.x, handlers.y, handlers.z):
        h2.add_handler(second)
