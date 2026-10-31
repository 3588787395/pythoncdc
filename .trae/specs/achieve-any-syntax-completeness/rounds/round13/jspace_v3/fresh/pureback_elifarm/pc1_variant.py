def f(items):
    out = None
    for x in items:
        d = x.get('k')
        if d is not None:
            if isinstance(d, int):
                out = d
                break
            elif hasattr(d, 'a') and hasattr(d, 'b'):
                out = d
                continue
    return out
