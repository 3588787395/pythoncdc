def f(wrapped, assigned):
    out = []
    for attr in assigned:
        try:
            value = getattr(wrapped, attr)
        except AttributeError:
            pass
        else:
            setattr(wrapped, attr, value)
            out.append(attr)
    return out
