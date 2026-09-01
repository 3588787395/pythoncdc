# Source Generated with Decompyle++ (Python version)
# File: repro_11.pyc (Python 3.11)

def repro_11(condition, path, items):
    if condition:
        for item in items:
            if item == '':
                pass
            continue
        else:
            try:
                os.unlink(path)
                log('warning')
            except:
                return None
    else:
        log('info')
