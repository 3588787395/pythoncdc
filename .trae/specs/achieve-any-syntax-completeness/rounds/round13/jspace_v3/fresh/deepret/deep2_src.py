def f(d, cond):
    for k, v in d.items():
        for uri in v:
            if cond(uri):
                return uri
    return None
