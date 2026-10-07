def n8p19(a):
    try:
        with CM(a):
            with open(a) as fp:
                r = rd(fp)
            w(fa(r))
            return None
    except Exception as e:
        lg(e)
        return None
