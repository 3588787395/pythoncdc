def setup(self, engine):
    import ptvsd
    engine.config.other.enable_debug = config.timeout or 10
