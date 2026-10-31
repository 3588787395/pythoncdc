def f(members):
    body = {t[0]: t[1] for t in members}
    body['__module__'] = 'm'
    return body
