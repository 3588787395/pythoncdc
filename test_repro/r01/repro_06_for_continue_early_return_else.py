def f(hosts, exclude_host):
    try:
        for host in hosts:
            if host == exclude_host:
                continue
            resp = query(host)
            code = resp.get('code', -1)
            if code != 0:
                log('failed: %s' % host)
                continue
            return {'error_no': 0, 'host': host}
        return {'error_no': -1, 'info': 'no valid host'}
        return None
    except BaseException:
        return {'error_no': -1, 'info': 'exception'}

def query(h):
    return {'code': 0}

def log(msg):
    pass
