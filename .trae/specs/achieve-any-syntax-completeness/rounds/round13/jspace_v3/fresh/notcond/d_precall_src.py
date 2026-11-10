def f(code, m, req, fp, newurl):
    m = req.get_method()
    if (not (code in (301, 302, 303, 307, 308) and m in ('GET', 'HEAD')
             or code in (301, 302, 303) and m == 'POST')):
        raise ValueError(req.full_url, code, m)
    return newurl
