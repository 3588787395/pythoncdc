# Source Generated with Decompyle++ (Python version)
# File: fi1.pyc (Python 3.11)

def find(mro, registry, cls_mro):
    match = None
    for t in mro:
        if match is not None:
            if t not in cls_mro:
                if match not in cls_mro:
                    if issubclass(match, t):
                        raise RuntimeError('Ambiguous: {} or {}'.format(match, t))
            else:
                break
            if t in registry and t not in cls_mro and match not in cls_mro and not issubclass(match, t):
                continue
            return registry.get(match)
        elif t in registry:
            match = t
