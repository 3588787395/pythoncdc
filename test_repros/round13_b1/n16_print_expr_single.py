if True:
    1 + 2
    f"{3}"
    (lambda v: v)(4)
    def nb(a, b, g, seq):
        while seq:
            if a and b:
                g()
            seq = seq[1:]
    nb
