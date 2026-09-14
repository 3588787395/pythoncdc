def save_testds_pattern(data, path):
    try:
        data.save(path)
    except BaseException:
        log('failed')
        try:
            debug(data)
        except BaseException:
            log('debug failed')
            try:
                data.backup(path)
            except BaseException:
                log('backup failed')
            return None
        return None
