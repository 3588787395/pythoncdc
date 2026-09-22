def store(payload):
    try:
        payload.write()
    except BaseException:
        print('write failed')
        return None
