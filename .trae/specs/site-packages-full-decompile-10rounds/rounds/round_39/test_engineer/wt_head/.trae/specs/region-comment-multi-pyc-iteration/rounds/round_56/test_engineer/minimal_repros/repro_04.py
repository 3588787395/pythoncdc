def repro_04(cond):
    for i in range(10):
        if cond:
            try:
                x = 1
            except:
                pass
    else:
        return None
