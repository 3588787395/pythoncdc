def example(path, mode):
    try:
        if os.path.exists(path):
            with open(path, mode) as fp:
                data = fp.read()
            if data:
                return data
    except Exception:
        print('error')
    return None
