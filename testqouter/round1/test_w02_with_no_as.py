def test():
    import tempfile, os
    fd, path = tempfile.mkstemp()
    os.close(fd)
    with open(path, 'w'):
        pass
    result = os.path.exists(path)
    os.unlink(path)
    return result
