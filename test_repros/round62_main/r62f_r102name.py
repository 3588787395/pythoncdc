FLAG = '1'


def setup(handlers, formatter, engine):
    value = int(engine.a) if FLAG == '1' else 2
    first = builder(value, engine.b, encoding='UTF-8')
    second = builder(value, engine.c, encoding='UTF-8')
    first.formatter = formatter
    first = wrap_async(first)
    note_only(second)
    second = wrap_async(second)
    for h in (handlers.x, handlers.y):
        h.add_handler(first)
    for h in (handlers.x, handlers.y, handlers.z):
        h.add_handler(second)
    return first
