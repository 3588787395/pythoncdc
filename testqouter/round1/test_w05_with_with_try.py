def test():
    import tempfile, os
    fd, path = tempfile.mkstemp()
    os.close(fd)
    with open(path, 'w') as f:
        try:
            f.write('hello')
        except:
            f.write('error')
    result = open(path).read()
    os.unlink(path)
    return result
