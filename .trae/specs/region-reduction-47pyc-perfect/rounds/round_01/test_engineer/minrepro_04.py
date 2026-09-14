def nested_except_cleanup(fp):
    for item in fp:
        try:
            if item == 'target':
                item
                if fp is not None:
                    return fp.close()
                else:
                    return None
        except BaseException:
            pass
    if fp is not None:
        fp.close()
