def store(payload):
    try:
        payload.write()
    except BaseException:
        print('write failed')
        try:
            payload.dump()
        except BaseException:
            print('dump failed')
            return None
    print('done')
