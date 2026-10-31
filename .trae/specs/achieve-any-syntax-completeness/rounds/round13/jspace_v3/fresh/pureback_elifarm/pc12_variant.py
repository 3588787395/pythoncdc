def f(keys, sk, ck, md):
    failed = []
    for method in ('a', 'b', 'c'):
        if method in sk and method in ck:
            continue
        elif method not in sk and method not in ck:
            x = getattr(md, method, None)
            if x != 1:
                failed.append(x)
        else:
            pass
    for method in ('d', 'e'):
        if method in sk:
            continue
        elif method in ck:
            failed.append(method)
        else:
            pass
    return failed
