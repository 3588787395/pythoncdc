def n8p24(a):
    try:
        with CM(a):
            with open(a) as fp:
                r = rd(fp)
    except Exception as e:
        lg(e)
