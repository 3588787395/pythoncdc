from contextlib import contextmanager
@contextmanager
def my_context():
    try:
        yield
    except:
        raise
