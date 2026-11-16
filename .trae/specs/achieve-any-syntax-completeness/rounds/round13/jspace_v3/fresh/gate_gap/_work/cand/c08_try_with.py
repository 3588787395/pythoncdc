def _host():
    pass

def outer(fn):
    try:
        with fn() as h:
            return h.read()
    except ValueError:
        return None
    except (TypeError, KeyError) as e:
        raise
    finally:
        pass
