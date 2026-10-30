def find(mro, registry, cls_mro):
    match = None
    for t in mro:
        if match is not None:
            if (t in registry and t not in cls_mro
                    and match not in cls_mro
                    and not issubclass(match, t)):
                raise RuntimeError("Ambiguous: {} or {}".format(match, t))
            break
        if t in registry:
            match = t
    return registry.get(match)
