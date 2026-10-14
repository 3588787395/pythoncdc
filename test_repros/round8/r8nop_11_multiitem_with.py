def n8p11(a):
    with open(a) as fp, open(a + '.tmp') as fq:
        r = fp.read()
        w = fq.write(r)
    return w
