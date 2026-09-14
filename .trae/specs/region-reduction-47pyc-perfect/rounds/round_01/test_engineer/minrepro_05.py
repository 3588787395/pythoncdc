def bare_except_with_return_in_body(path):
    try:
        f = open(path, 'r')
        data = f.read()
    except BaseException:
        return None
    return data
