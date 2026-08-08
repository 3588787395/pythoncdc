def repro_11(condition, path, items):
    if condition:
        for item in items:
            if item == '':
                pass
        try:
            os.unlink(path)
            log('warning')
        except:
            pass
    else:
        log('info')
