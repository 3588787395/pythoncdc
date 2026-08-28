def f(engine):
    if engine.debug:
        import ptvsd
        engine.x = ptvsd.y() or 10
        engine.z = 1
