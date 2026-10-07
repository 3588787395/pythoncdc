def n8p25(a):
    try:
        with CM(a):
            with open(a) as fp:
                r = rd(fp)
            w(fa(r))
    except Exception as e:
        lg(e)
        return None
