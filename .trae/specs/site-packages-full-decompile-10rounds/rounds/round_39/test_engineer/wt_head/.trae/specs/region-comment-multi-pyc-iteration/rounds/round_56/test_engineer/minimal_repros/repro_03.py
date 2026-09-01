def repro_03(items):
    for item in items:
        if item == 'a':
            try:
                x = 1
            except:
                pass
        elif item == 'b':
            pass
    else:
        return None
