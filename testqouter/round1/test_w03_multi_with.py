def test():
    import tempfile, os
    fd1, p1 = tempfile.mkstemp()
    fd2, p2 = tempfile.mkstemp()
    os.close(fd1); os.close(fd2)
    with open(p1, 'w') as f1, open(p2, 'w') as f2:
        f1.write('a')
        f2.write('b')
    result = open(p1).read() + open(p2).read()
    os.unlink(p1); os.unlink(p2)
    return result
