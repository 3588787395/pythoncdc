def test():
    import tempfile, os
    fd, path = tempfile.mkstemp()
    os.close(fd)
    try:
        with open(path, 'w') as f:
            f.write('hello')
    except:
        open(path, 'w').write('error')
    result = open(path).read()
    os.unlink(path)
    return result
