def setup(self, engine):
    if engine.config.other.enable_debug:
        import ptvsd
        if get_python_version() == '3.11':
            ptvsd.reset()
        engine.config.other.enable_debug = config.timeout or 10
