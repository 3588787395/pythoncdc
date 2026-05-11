def test():
    import tempfile, os
    fd, path = tempfile.mkstemp()
    os.close(fd)
    with open(path, 'w') as f:
        f.write('hello')
    result = open(path).read()
    os.unlink(path)
    return result
