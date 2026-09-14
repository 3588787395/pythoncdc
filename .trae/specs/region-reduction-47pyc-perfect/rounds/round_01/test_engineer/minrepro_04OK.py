# Source Generated with Decompyle++ (Python version)
# File: minrepro_04.pyc (Python 3.11)

def nested_except_cleanup(fp):
    for item in fp:
        try:
            if item == 'target':
                item
                if fp is None:
                    return None
                    break
                return fp.close()
            continue
        except BaseException:
            pass
    else:
        if fp is not None:
            fp.close()
            return None
        return None
