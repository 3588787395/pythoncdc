def store(payload):
    try:
        payload.write()
        return None
    except BaseException:
        print('write failed')
        try:
            payload.dump()
        except BaseException:
            print('dump failed')
