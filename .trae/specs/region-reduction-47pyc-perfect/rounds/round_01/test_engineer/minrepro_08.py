def with_statement_in_try(x):
    try:
        with open(x, 'r') as f:
            data = f.read()
            if data is None:
                return None
    except BaseException:
        return None
    return data
