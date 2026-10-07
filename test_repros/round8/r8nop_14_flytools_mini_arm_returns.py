def n8p14(a, log):
    try:
        with CM(a):
            with open(a) as fp:
                r = rd(fp)
            w(fa(r))
            return None
    except Exception as e:
        if log:
            if r:
                log.info(e)
            elif not r:
                log.warn(e)
                return None
            else:
                return None
            return None
        else:
            return None
