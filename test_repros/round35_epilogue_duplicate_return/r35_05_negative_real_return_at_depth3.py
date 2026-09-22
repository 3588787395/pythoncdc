def store(payload):
    try:
        payload.write()
        return None
    except BaseException:
        print('write failed')
        try:
            payload.dump()
            return None
        except BaseException:
            print('dump failed')
            try:
                payload.text()
            except BaseException:
                print('text failed')
                return None
