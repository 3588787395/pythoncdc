def rs(seq):
    def inner():
        return seq
    out = [i for i in seq if i]
    return inner, out
